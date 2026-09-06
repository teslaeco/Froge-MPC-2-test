// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { DatabaseSync, type SQLInputValue } from 'node:sqlite'
import { readFileSync } from 'node:fs'
import { blenderApi, type BlenderEnv, validateEndpoint } from '../blender/server'

let db: DatabaseSync, env: BlenderEnv
const files = new Map<string, ArrayBuffer>()
const endpoint = 'https://froge-test.trycloudflare.com', token = 'private-worker-token-'.repeat(3)
const id = '12345678-1234-4234-8234-123456789abc'
function request(path: string, method = 'GET', body?: unknown, owner = 'owner-a', origin = 'https://studio.test') {
  return blenderApi(new Request('https://studio.test/api/blender/' + path, { method, headers: { 'oai-authenticated-user-id': owner, origin, 'content-type': 'application/json' }, ...(body === undefined ? {} : { body: JSON.stringify(body) }) }), env)
}
async function pair() {
  vi.stubGlobal('fetch', vi.fn(async () => Response.json({ token })))
  expect((await request('connection', 'POST', { endpoint, code: 'a'.repeat(32) })).status).toBe(200)
}
async function submit() {
  vi.stubGlobal('fetch', vi.fn(async () => Response.json({ state: 'queued' }, { status: 202 })))
  return request('jobs', 'POST', { id, prompt: 'Duży dąb z korą i liśćmi' })
}
function minimalGlb() {
  const json = new TextEncoder().encode('{"asset":{"version":"2.0"}} ')
  const bytes = new ArrayBuffer(20 + json.length), view = new DataView(bytes)
  view.setUint32(0, 0x46546c67, true); view.setUint32(4, 2, true); view.setUint32(8, bytes.byteLength, true)
  view.setUint32(12, json.length, true); view.setUint32(16, 0x4e4f534a, true); new Uint8Array(bytes, 20).set(json)
  return bytes
}
beforeEach(() => {
  db = new DatabaseSync(':memory:'); files.clear()
  db.exec(readFileSync('drizzle/0001_blender_generation.sql', 'utf8'))
  env = {
    BLENDER_SETTINGS_KEY: '12'.repeat(32),
    DB: { prepare(sql) {
      let args: SQLInputValue[] = []
      const statement = {
        bind(...values: unknown[]) { args = values as SQLInputValue[]; return statement },
        async first<T>() { return (db.prepare(sql).get(...args) || null) as T | null },
        async all<T>() { return { results: db.prepare(sql).all(...args) as T[] } },
        async run() { return { meta: { changes: Number(db.prepare(sql).run(...args).changes) } } },
      }
      return statement
    } },
    BUCKET: {
      async put(key, bytes) { files.set(key, bytes) },
      async get(key) { const bytes = files.get(key); return bytes ? { body: new Response(bytes).body! } : null },
      async head(key) { return files.has(key) },
    },
  }
})
afterEach(() => { db.close(); vi.unstubAllGlobals() })

describe('private Blender request lifecycle with real SQLite', () => {
  it('requires authentication, same-origin writes and the restricted HTTPS tunnel namespace', async () => {
    expect((await request('jobs', 'GET', undefined, '')).status).toBe(401)
    expect((await request('connection', 'POST', {}, 'owner-a', 'https://other.test')).status).toBe(403)
    for (const url of ['http://127.0.0.1:8765', 'https://example.com', endpoint + '/v1/health', 'https://x.y.trycloudflare.com', endpoint + '?x=1', 'https://user:pass@froge-test.trycloudflare.com']) expect(() => validateEndpoint(url)).toThrow()
    expect(validateEndpoint(endpoint + '/')).toBe(endpoint)
    expect((await request('connection', 'POST', null)).status).toBe(400)
  })
  it('encrypts the worker token and isolates jobs and downloads by signed-in owner', async () => {
    await pair()
    const stored = db.prepare('SELECT credential FROM blender_connections').get()!
    expect(String(stored.credential)).not.toContain(token)
    vi.stubGlobal('fetch', vi.fn(async (_url, init) => {
      expect(init.headers.Authorization).toBe('Bearer ' + token)
      return Response.json({ ready: true, model: 'local-coder', detail: 'ready' })
    }))
    const health = await (await request('connection')).json()
    expect(health.ready).toBe(true); expect(JSON.stringify(health)).not.toContain(token)
    await submit()
    expect(await (await request('jobs', 'GET', undefined, 'owner-b')).json()).toEqual({ jobs: [] })
    expect((await request('jobs/' + id, 'GET', undefined, 'owner-b')).status).toBe(404)
    expect((await request('jobs/' + id + '/model', 'GET', undefined, 'owner-b')).status).toBe(404)
  })
  it('sends OpenAI setup only to the paired worker and returns no API credential', async () => {
    const apiKey = 'sk-fixture-' + 'a'.repeat(30)
    expect((await request('ai', 'POST', { provider: 'openai', apiKey })).status).toBe(409)
    await pair()
    const upstream = vi.fn(async (_url, init) => {
      expect(String(_url)).toBe(endpoint + '/v1/ai')
      expect(init.redirect).toBe('manual')
      expect(init.headers.Authorization).toBe('Bearer ' + token)
      expect(JSON.parse(init.body)).toEqual({ provider: 'openai', apiKey })
      return Response.json({ saved: true, apiKey })
    })
    vi.stubGlobal('fetch', upstream)
    expect((await request('ai', 'POST', { provider: 'openai', apiKey }, 'owner-b')).status).toBe(409)
    expect((await request('ai', 'POST', { provider: 'openai', apiKey }, 'owner-a', 'https://other.test')).status).toBe(403)
    const response = await request('ai', 'POST', { provider: 'openai', apiKey })
    expect(await response.json()).toEqual({ saved: true })
    expect(upstream).toHaveBeenCalledTimes(1)
    expect(JSON.stringify(db.prepare('SELECT * FROM blender_connections').all())).not.toContain(apiKey)
    expect((await request('ai', 'POST', { provider: 'openai', apiKey: apiKey + '\n' })).status).toBe(400)
  })
  it.each([301, 302, 303, 307, 308])('refuses HTTP %i during pairing without forwarding the code or storing a credential', async status => {
    const upstream = vi.fn(async (_url, init) => {
      expect(init.redirect).toBe('manual')
      return new Response(null, { status, headers: { Location: 'https://another-server.example/collect' } })
    })
    vi.stubGlobal('fetch', upstream)
    const response = await request('connection', 'POST', { endpoint, code: 'a'.repeat(32) })
    expect(response.status).toBe(502)
    expect((await response.json()).error).toContain('przekierowanie')
    expect(upstream).toHaveBeenCalledTimes(1)
    expect(db.prepare('SELECT COUNT(*) AS total FROM blender_connections').get()!.total).toBe(0)
  })
  it('reports a transport error without exposing a credential or pretending pairing succeeded', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('transport error: ' + token) }))
    const response = await request('connection', 'POST', { endpoint, code: 'a'.repeat(32) })
    expect(response.status).toBe(502)
    const data = await response.json()
    expect(data.error).toContain('Oracle')
    expect(JSON.stringify(data)).not.toContain(token)
    expect(db.prepare('SELECT COUNT(*) AS total FROM blender_connections').get()!.total).toBe(0)
  })
  it('submits an exact prompt once and persists the returned GLB for the same owner', async () => {
    await pair(); expect((await submit()).status).toBe(202)
    const remote = vi.mocked(fetch)
    expect(JSON.parse(String(remote.mock.calls[0][1]?.body))).toEqual({ id, prompt: 'Duży dąb z korą i liśćmi' })
    expect((await request('jobs', 'POST', { id, prompt: 'Duży dąb z korą i liśćmi' })).status).toBe(200)
    expect(remote).toHaveBeenCalledTimes(1)
    expect((await request('jobs', 'POST', { id, prompt: 'Smok' })).status).toBe(409)
    const bytes = minimalGlb()
    vi.stubGlobal('fetch', vi.fn(async url => String(url).endsWith('/model') ? new Response(bytes) : Response.json({ state: 'succeeded', detail: 'ready' })))
    expect(await (await request('jobs/' + id)).json()).toMatchObject({ job: { state: 'succeeded', hasModel: true } })
    expect(files.get('owner-a/' + id + '.glb')).toEqual(bytes)
    expect(await (await request('jobs/' + id + '/model')).arrayBuffer()).toEqual(bytes)
  })
  it('preserves cancellation when a completion response was already in flight', async () => {
    await pair(); await submit()
    vi.stubGlobal('fetch', vi.fn(async url => {
      if (String(url).endsWith('/model')) {
        db.prepare("UPDATE blender_jobs SET state='cancelled' WHERE id=?").run(id)
        return new Response(minimalGlb())
      }
      return Response.json({ state: 'succeeded' })
    }))
    expect(await (await request('jobs/' + id)).json()).toMatchObject({ job: { state: 'cancelled', hasModel: false } })
  })
  it('marks a missing remote job or invalid artifact as failed without substituting a sample', async () => {
    await pair(); await submit()
    vi.stubGlobal('fetch', vi.fn(async url => String(url).endsWith('/model') ? new Response('bad glb') : Response.json({ state: 'succeeded' })))
    expect(await (await request('jobs/' + id)).json()).toMatchObject({ job: { state: 'failed', hasModel: false } })
    expect(files.size).toBe(0)
    db.prepare("UPDATE blender_jobs SET state='submitting' WHERE id=?").run(id)
    vi.stubGlobal('fetch', vi.fn(async () => Response.json({ error: 'Missing' }, { status: 404 })))
    expect(await (await request('jobs/' + id)).json()).toMatchObject({ job: { state: 'failed', hasModel: false } })
  })
})
