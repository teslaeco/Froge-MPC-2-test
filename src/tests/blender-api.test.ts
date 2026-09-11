/// <reference types="node" />
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
  vi.stubGlobal('fetch', vi.fn(async url => Response.json(String(url).endsWith('/health') ? { connectorVersion: 11 } : { state: 'queued' }, { status: 202 })))
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
  db.exec(readFileSync('drizzle/0002_blender_reference_photos.sql', 'utf8'))
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
  it('configures Meshy separately and never returns or stores its key in D1', async () => {
    await pair()
    const key = 'offline-fixture-meshy-key-123456789'
    const upstream = vi.fn(async (_url: RequestInfo | URL, _init?: RequestInit) => Response.json({ saved: true }))
    vi.stubGlobal('fetch', upstream)
    expect((await request('image3d', 'POST', { provider: 'meshy', apiKey: key, textureResolution: '8k' }, 'owner-a', 'https://foreign.test')).status).toBe(403)
    expect(upstream).not.toHaveBeenCalled()
    const response = await request('image3d', 'POST', { provider: 'meshy', apiKey: key, textureResolution: '8k' })
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ saved: true })
    expect(upstream.mock.calls[0][0]).toBe(endpoint + '/v1/image3d')
    expect(JSON.stringify(db.prepare('SELECT * FROM blender_connections').all())).not.toContain(key)
    expect(db.prepare('SELECT COUNT(*) AS n FROM blender_jobs').get()?.n).toBe(0)
  })
  it('streams actual FBX bytes only to the model owner', async () => {
    await pair(); await submit()
    db.prepare("UPDATE blender_jobs SET state='succeeded',artifact='ready.glb' WHERE id=?").run(id)
    const bytes = new TextEncoder().encode('offline FBX transport fixture')
    const upstream = vi.fn(async (_url: RequestInfo | URL, _init?: RequestInit) => new Response(bytes, { headers: { 'content-length': String(bytes.length) } }))
    vi.stubGlobal('fetch', upstream)
    expect((await request(`jobs/${id}/exports/fbx`, 'GET', undefined, 'owner-b')).status).toBe(404)
    expect(upstream).not.toHaveBeenCalled()
    const response = await request(`jobs/${id}/exports/fbx`)
    expect(response.status).toBe(200)
    expect(response.headers.get('content-disposition')).toContain('model.fbx')
    expect(response.headers.get('cache-control')).toBe('private, no-store')
    expect(new Uint8Array(await response.arrayBuffer())).toEqual(bytes)
    expect(upstream.mock.calls[0][0]).toBe(endpoint + `/v1/jobs/${id}/exports/fbx`)
  })
  it('forwards a free image3d resume explicitly without resending new photos', async () => {
    await pair()
    const upstream = vi.fn(async (url, _init) => Response.json(String(url).endsWith('/health') ? { connectorVersion:21, image3dRevision:1, image3dReady:true, sceneReplay:true } : {state:'queued'}))
    vi.stubGlobal('fetch',upstream)
    expect((await request('jobs','POST',{id,prompt:'Reference model',photos:[photo]})).status).toBe(202)
    db.prepare("UPDATE blender_jobs SET state='failed',detail='Meshy download interrupted' WHERE id=?").run(id)
    upstream.mockClear()
    const next = id.slice(0,-1)+'d'
    const resume = {id:next,prompt:'Reference model',sourceJobId:id,resumeImage3d:true}
    expect((await request('jobs','POST',resume)).status).toBe(202)
    const call = upstream.mock.calls.find(([url])=>String(url).endsWith('/v1/jobs'))!
    expect(JSON.parse(call[1].body)).toEqual(resume)
  })
  it('accepts 5000 UTF-16 units only on a capable worker and rejects 5001 before submitting', async () => {
    await pair()
    const upstream=vi.fn(async url=>Response.json(String(url).endsWith('/health') ? {connectorVersion:19,promptMaxLength:5000} : {state:'queued'}))
    vi.stubGlobal('fetch',upstream)
    expect((await request('jobs','POST',{id,prompt:'x'.repeat(5000)})).status).toBe(202)
    upstream.mockClear()
    expect((await request('jobs','POST',{id:id.slice(0,-1)+'d',prompt:'x'.repeat(5001)})).status).toBe(400)
    expect(upstream).not.toHaveBeenCalled()
  })
  it('rejects a couture request on an older worker without creating a paid job', async () => {
    await pair()
    const upstream=vi.fn(async()=>Response.json({connectorVersion:16,portraitRevision:1,provider:'openai',photoInput:true}))
    vi.stubGlobal('fetch',upstream)
    const response=await request('jobs','POST',{id,prompt:'Kobieta, dopasowana suknia i wachlarz'})
    expect(response.status).toBe(409)
    expect((await response.json()).error).toContain('v19')
    expect(upstream).toHaveBeenCalledTimes(1)
    expect(db.prepare('SELECT COUNT(*) AS n FROM blender_jobs').get()?.n).toBe(0)
  })
  // Small JPEG framing fixture; these tests verify transport, not visual quality.
  const image = new Uint8Array([255,216,255,192,0,11,8,0,1,0,1,1,1,17,0,255,218,0,2,0,255,217])
  const photo = { name: 'front.jpg', view: 'front', dataUrl: 'data:image/jpeg;base64,' + Buffer.from(image).toString('base64') }
  it('requires a neural connection and preserves input resolution on replay', async () => {
    await pair()
    const capabilities = { connectorVersion:21, image3dRevision:1, image3dReady:false, portraitRevision:2, provider:'openai', photoInput:true,
      referenceQualityRevision:1, materialQualityRevision:0, sceneReplay:true }
    const upstream=vi.fn(async (url, _init) => Response.json(String(url).endsWith('/health') ? capabilities : {state:'queued'}))
    vi.stubGlobal('fetch',upstream)
    const input={id,prompt:'Model z referencji',photos:[{...photo,textureMaxSize:8192}]}
    expect((await request('jobs','POST',input)).status).toBe(409)
    expect(upstream.mock.calls.some(([url])=>String(url).endsWith('/v1/jobs'))).toBe(false)
    capabilities.materialQualityRevision=2; capabilities.image3dReady=true
    expect((await request('jobs','POST',input)).status).toBe(202)
    const posted=JSON.parse(upstream.mock.calls.find(([url])=>String(url).endsWith('/v1/jobs'))![1].body)
    expect(posted.photos[0].textureMaxSize).toBe(8192)
    const health=await (await request('connection')).json()
    expect(health.materialQualityRevision).toBe(2)
    db.prepare("UPDATE blender_jobs SET state='failed' WHERE id=?").run(id)
    const rebuilt=id.slice(0,-1)+'d'
    expect((await request('jobs','POST',{id:rebuilt,prompt:input.prompt,sourceJobId:id})).status).toBe(202)
    expect((await (await request(`jobs/${rebuilt}`)).json()).job.referencePhotos[0].textureMaxSize).toBe(8192)
  })
  it('preserves legacy photo metadata but requires image-to-3D instead of a face fitter', async () => {
    await pair()
    const digest = Buffer.from(await crypto.subtle.digest('SHA-256', image)).toString('hex')
    const measured = { ...photo, faceLandmarks: { revision: 1, width: 1, height: 1, imageSha256: digest, points: Array.from({length:478}, () => [.5,.5,0]) } }
    const capabilities = { connectorVersion:21,image3dRevision:1,image3dReady:false,portraitRevision:2,provider:'openai',photoInput:true,faceFitRevision:0 }
    const upstream = vi.fn(async (url, _init) => Response.json(String(url).endsWith('/health') ? capabilities : {state:'queued'}))
    vi.stubGlobal('fetch', upstream)
    expect((await request('jobs','POST',{id,prompt:'Postać ze zdjęcia',photos:[measured]})).status).toBe(409)
    expect(db.prepare('SELECT COUNT(*) AS n FROM blender_jobs').get()?.n).toBe(0)
    capabilities.image3dReady=true
    const accepted=await request('jobs','POST',{id,prompt:'Postać ze zdjęcia',photos:[measured]})
    expect(accepted.status).toBe(202)
    expect(JSON.stringify(await accepted.json())).not.toContain('points')
    const retryId='12345678-1234-4234-8234-123456789abd'
    expect((await request('jobs','POST',{id:retryId,prompt:'Postać ze zdjęcia',referenceJobId:id})).status).toBe(202)
    const calls=upstream.mock.calls.filter(([url])=>String(url).endsWith('/v1/jobs'))
    expect(JSON.parse(calls[1][1].body).photos[0].faceLandmarks).toEqual(measured.faceLandmarks)
  })
  it('copies private photo history for a saved-plan replay but sends only its source ID to Oracle', async () => {
    await pair()
    const capabilities = { connectorVersion: 21, image3dRevision: 1, image3dReady: true, portraitRevision: 1, provider: 'openai', photoInput: true, sceneReplay: false }
    const upstream = vi.fn(async (url, _init) => Response.json(String(url).endsWith('/health') ? capabilities : { state: 'queued' }))
    vi.stubGlobal('fetch', upstream)
    expect((await request('jobs', 'POST', { id, prompt: 'Girl from photo', photos: [photo] })).status).toBe(202)
    db.prepare("UPDATE blender_jobs SET state='failed',detail='Use at most 8 materials and 8 images.' WHERE id=?").run(id)
    const rebuilt = '12345678-1234-4234-8234-123456789abd'
    const replay = { id: rebuilt, prompt: 'Girl from photo', sourceJobId: id }
    upstream.mockClear()
    expect((await request('jobs', 'POST', replay)).status).toBe(409)
    expect(upstream.mock.calls.some(([url]) => String(url).endsWith('/v1/jobs'))).toBe(false)
    capabilities.sceneReplay = true; capabilities.provider = 'ollama'; capabilities.photoInput = false
    const response = await request('jobs', 'POST', replay)
    expect(response.status).toBe(202)
    expect((await response.json()).job.referencePhotos).toHaveLength(1)
    expect(JSON.parse(upstream.mock.calls.find(([url]) => String(url).endsWith('/v1/jobs'))![1].body)).toEqual(replay)
    expect(files.get(`owner-a/${rebuilt}/reference-0.jpg`)).toEqual(image.buffer)
    expect((await request(`jobs/${rebuilt}/photos/0`, 'GET', undefined, 'owner-b')).status).toBe(404)
    expect((await request('jobs', 'POST', replay)).status).toBe(200)
    expect(upstream.mock.calls.filter(([url]) => String(url).endsWith('/v1/jobs'))).toHaveLength(1)
    expect(db.prepare('SELECT state FROM blender_jobs WHERE id=?').get(id)?.state).toBe('failed')
  })
  it('persists reference bytes privately, restores them in history and repeats the same photographs', async () => {
    await pair()
    const upstream = vi.fn(async (url, _init) => Response.json(String(url).endsWith('/health') ? { connectorVersion: 21, image3dRevision: 1, image3dReady: true, portraitRevision: 1, provider: 'openai', photoInput: true } : { state: 'queued' }))
    vi.stubGlobal('fetch', upstream)
    const input = { id, prompt: 'Model z referencji', photos: [photo, { ...photo, name: 'side.jpg', view: 'side' }] }
    const response = await request('jobs', 'POST', input)
    expect(response.status).toBe(202)
    const result = await response.json()
    expect(result.job.referencePhotos).toHaveLength(2)
    expect(JSON.stringify(result)).not.toContain('base64')
    expect(JSON.parse(String(upstream.mock.calls.find(([url]) => String(url).endsWith('/v1/jobs'))?.[1]?.body))).toEqual(input)
    expect((await request(`jobs/${id}/photos/0`, 'GET', undefined, 'owner-b')).status).toBe(404)
    const own = await request(`jobs/${id}/photos/0`)
    expect(own.headers.get('content-type')).toBe('image/jpeg')
    expect(own.headers.get('cache-control')).toContain('private')
    expect(new Uint8Array(await own.arrayBuffer())).toEqual(image)
    expect(JSON.stringify(db.prepare('SELECT reference_photos FROM blender_jobs').get())).not.toContain('base64')
    expect((await (await request('jobs')).json()).jobs[0].referencePhotos[1].view).toBe('side')
    const called = upstream.mock.calls.length
    expect((await request('jobs', 'POST', input)).status).toBe(200)
    expect(upstream).toHaveBeenCalledTimes(called)
    expect((await request('jobs', 'POST', { ...input, photos: [{ ...photo, view: 'back' }] })).status).toBe(409)
    db.prepare("UPDATE blender_jobs SET state='failed' WHERE id=?").run(id)
    const retryId = '12345678-1234-4234-8234-123456789abd'
    expect((await request('jobs', 'POST', { id: retryId, prompt: input.prompt, referenceJobId: id })).status).toBe(202)
    const sent = upstream.mock.calls.filter(([url]) => String(url).endsWith('/v1/jobs')).at(-1)!
    expect(JSON.parse(String(sent[1]?.body))).toEqual({ ...input, id: retryId })
    expect(files.get(`owner-a/${retryId}/reference-0.jpg`)).toEqual(image.buffer)
    db.prepare('DELETE FROM blender_connections').run()
    expect((await request(`jobs/${id}/photos/0`)).status).toBe(200)
  })
  it.each([{ connectorVersion: 13, provider: 'openai', photoInput: true }, { connectorVersion: 14, provider: 'openai', photoInput: true }, { connectorVersion: 15, provider: 'openai', photoInput: true }, { connectorVersion: 15, portraitRevision: 1, provider: 'openai' }, { connectorVersion: 15, portraitRevision: 1, provider: 'ollama', photoInput: true }])('never sends photographs to a worker without compatible vision capability: %j', async capabilities => {
    await pair()
    const upstream = vi.fn(async () => Response.json(capabilities))
    vi.stubGlobal('fetch', upstream)
    const response = await request('jobs', 'POST', { id, prompt: 'Model', photos: [photo] })
    expect(response.status).toBe(409)
    expect(upstream).toHaveBeenCalledTimes(1)
    expect(db.prepare('SELECT COUNT(*) AS total FROM blender_jobs').get()!.total).toBe(0)
    expect(files.size).toBe(0)
  })
  it('rejects remote image URLs, malformed JPEGs, too many photographs and oversized decoded images', async () => {
    await pair()
    const upstream = vi.fn(); vi.stubGlobal('fetch', upstream)
    const oversized = image.slice(); oversized[9] = 32; oversized[10] = 1
    for (const photos of [[{ ...photo, dataUrl: 'https://example.test/image.jpg' }], [{ ...photo, dataUrl: 'data:image/svg+xml;base64,PHN2Zz4=' }], [{ ...photo, dataUrl: 'data:image/jpeg;base64,' + Buffer.from(oversized).toString('base64') }], Array(5).fill(photo)]) {
      expect((await request('jobs', 'POST', { id, prompt: 'Model', photos })).status).toBe(422)
    }
    expect(upstream).not.toHaveBeenCalled()
    expect(files.size).toBe(0)
  })
  it('does not submit a photo generation when durable image storage fails', async () => {
    await pair()
    const upstream = vi.fn(async () => Response.json({ connectorVersion: 21, image3dRevision: 1, image3dReady: true, portraitRevision: 1, provider: 'openai', photoInput: true }))
    vi.stubGlobal('fetch', upstream)
    env.BUCKET!.put = async () => { throw new Error('storage unavailable') }
    expect((await request('jobs', 'POST', { id, prompt: 'Model', photos: [photo] })).status).toBe(503)
    expect(upstream).toHaveBeenCalledTimes(1)
    expect(db.prepare('SELECT state FROM blender_jobs').get()!.state).toBe('failed')
  })
  it('restores a verified email-only session to its existing encrypted connection and jobs', async () => {
    await pair(); await submit()
    const original = db.prepare('SELECT * FROM blender_connections').get()
    env.SITE_IDENTITY_ALIASES = JSON.stringify({ 'owner@example.test': 'owner-a' })
    const asSession = (path: string, email: string, stableId?: string, method = 'GET', origin = 'https://studio.test') => blenderApi(new Request('https://studio.test/api/blender/' + path, {
      method, headers: { 'oai-authenticated-user-email': email, origin, ...(stableId ? { 'oai-authenticated-user-id': stableId } : {}) },
    }), env)
    vi.stubGlobal('fetch', vi.fn(async (_url, init) => {
      expect(init.headers.Authorization).toBe('Bearer ' + token)
      return Response.json({ ready: true, connectorVersion: 11 })
    }))
    expect(await (await asSession('connection', 'owner@example.test')).json()).toMatchObject({ connected: true, ready: true })
    expect(await (await asSession('jobs', 'owner@example.test')).json()).toMatchObject({ jobs: [{ id }] })
    expect(await (await asSession('jobs', 'owner@example.test', 'owner-b')).json()).toEqual({ jobs: [] })
    expect((await asSession('jobs/' + id, 'owner@example.test', 'owner-b')).status).toBe(404)
    expect((await asSession('jobs', 'stranger@example.test')).status).toBe(401)
    expect((await asSession('jobs', 'owner@example.test', undefined, 'POST', 'https://other.test')).status).toBe(403)
    expect(db.prepare('SELECT * FROM blender_connections').get()).toEqual(original)
  })
  it('logs only bounded worker capabilities so a failed update can be diagnosed without secrets', async () => {
    await pair()
    const log = vi.spyOn(console, 'info').mockImplementation(() => {})
    try {
      vi.stubGlobal('fetch', vi.fn(async () => Response.json({ ready: true, detail: 'private detail', model: 'private model', provider: 'ollama' })))
      const response = await request('connection')
      expect(response.status).toBe(200)
      expect(log).toHaveBeenCalledWith('FROGE_ORACLE_HEALTH', JSON.stringify({ connectorVersion: 1, provider: 'ollama', ready: true, photoInput: false, rendererRevision: 1, portraitRevision: 0, characterStandard: 0, coutureRevision: 0, promptMaxLength: 2000, sceneReplay: false }))
      const recorded = JSON.stringify(log.mock.calls)
      expect(recorded).not.toContain(token)
      expect(recorded).not.toContain(endpoint)
      expect(recorded).not.toContain('private')
    } finally { log.mockRestore() }
  })
  it.each([5, 6])('rejects generation on worker v%i before queuing', async version => {
    await pair()
    const upstream = vi.fn(async () => Response.json({ connectorVersion: version, ready: true }))
    vi.stubGlobal('fetch', upstream)
    const response = await request('jobs', 'POST', { id, prompt: 'Dąb' })
    expect(response.status).toBe(409)
    expect((await response.json()).error).toContain('froge-oracle-update.zip (v14)')
    expect(db.prepare('SELECT COUNT(*) AS total FROM blender_jobs').get()!.total).toBe(0)
    expect(upstream).toHaveBeenCalledTimes(1)
  })
  it('rebuilds only the same owner failed script on a compatible worker', async () => {
    await pair(); await submit()
    db.prepare("UPDATE blender_jobs SET state='failed' WHERE id=?").run(id)
    const rebuilt = '12345678-1234-4234-8234-123456789abd'
    let version = 4
    const upstream = vi.fn(async (url, _init) => Response.json(String(url).endsWith('/pair') ? { token } : String(url).endsWith('/health') ? { connectorVersion: version } : { state: 'queued' }))
    vi.stubGlobal('fetch', upstream)
    expect((await request('connection', 'POST', { endpoint, code: 'a'.repeat(32) }, 'owner-b')).status).toBe(200)
    const input = { id: rebuilt, prompt: 'Duży dąb z korą i liśćmi', sourceJobId: id }
    expect((await request('jobs', 'POST', input, 'owner-b')).status).toBe(409)
    expect((await request('jobs', 'POST', { ...input, prompt: 'Inny model' })).status).toBe(409)
    expect((await request('jobs', 'POST', input)).status).toBe(409)
    version = 11
    expect((await request('jobs', 'POST', input)).status).toBe(202)
    const sent = upstream.mock.calls.find(([url]) => String(url).endsWith('/v1/jobs'))!
    expect(JSON.parse(sent[1].body)).toEqual(input)
    expect(db.prepare('SELECT state FROM blender_jobs WHERE id=?').get(id)?.state).toBe('failed')
  })
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
  it.each([7, 8, 9, 10, 11])('worker v%i submits the exact prompt once and persists its GLB for the same owner', async version => {
    await pair()
    vi.stubGlobal('fetch', vi.fn(async url => Response.json(String(url).endsWith('/health') ? { connectorVersion: version } : { state: 'queued' })))
    expect((await request('jobs', 'POST', { id, prompt: 'Duży dąb z korą i liśćmi' })).status).toBe(202)
    const remote = vi.mocked(fetch)
    expect(JSON.parse(String(remote.mock.calls.find(([url]) => String(url).endsWith('/v1/jobs'))?.[1]?.body))).toEqual({ id, prompt: 'Duży dąb z korą i liśćmi' })
    expect((await request('jobs', 'POST', { id, prompt: 'Duży dąb z korą i liśćmi' })).status).toBe(200)
    expect(remote).toHaveBeenCalledTimes(2)
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
    expect(await (await request('jobs/' + id)).json()).toMatchObject({ job: { state: 'submitting', hasModel: false } })
    db.prepare("UPDATE blender_jobs SET created='2026-01-01T00:00:00Z' WHERE id=?").run(id)
    expect(await (await request('jobs/' + id)).json()).toMatchObject({ job: { state: 'failed', hasModel: false } })
  })
})
