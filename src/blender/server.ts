import type { CommerceEnv } from '../commerce/server'
import { siteOwner, type SiteIdentityEnv } from '../auth/site-owner'
import { supportsGeneration, supportsPhotoGeneration, supportsPortraitQuality, requiresPortraitQuality, PORTRAIT_UPDATE_REASON, supportsCoutureQuality, requiresCoutureQuality, COUTURE_UPDATE_REASON } from './compatibility'
import { decodePhotoInputs, MAX_PHOTO_REQUEST_BYTES, MAX_REFERENCE_BYTES, type PhotoMetadata } from './photoReferences'

export type BlenderEnv = CommerceEnv & SiteIdentityEnv & { BLENDER_SETTINGS_KEY?: string }
type Connection = { owner: string; endpoint: string; credential: string }
type Job = { id: string; owner: string; endpoint: string; prompt: string; state: string; detail: string; artifact: string | null; created: string; updated: string; reference_photos?: string }
class ApiError extends Error { readonly status: number; constructor(message: string, status = 400) { super(message); this.status = status } }
const reply = (data: unknown, status = 200) => Response.json(data, { status, headers: { 'Cache-Control': 'private, no-store' } })
const uuid = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/
const maxGlb = 48 * 1024 * 1024

export function validateEndpoint(value: unknown): string {
  if (typeof value !== 'string') throw new ApiError('Wklej adres HTTPS serwera z instalatora.')
  let url: URL
  try { url = new URL(value.trim()) } catch { throw new ApiError('Nieprawidłowy adres serwera.') }
  // This installer uses Cloudflare's public Quick Tunnel namespace. No redirects,
  // IP literals, private hosts, arbitrary URLs, credentials or query strings.
  if (url.protocol !== 'https:' || !/^[a-z0-9]+(?:-[a-z0-9]+)*\.trycloudflare\.com$/.test(url.hostname) || url.port || url.username || url.password || url.pathname !== '/' || url.search || url.hash)
    throw new ApiError('Użyj adresu https://…trycloudflare.com wyświetlonego przez instalator.')
  return url.origin
}
async function boundedBody(body: ReadableStream<Uint8Array> | null, limit: number, expected?: number): Promise<ArrayBuffer> {
  if (!body) return new ArrayBuffer(0)
  const reader = body.getReader(), chunks: Uint8Array[] = []
  const exact = expected && Number.isSafeInteger(expected) && expected <= limit ? new Uint8Array(expected) : null
  let size = 0
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    size += value.byteLength
    if (size > limit) { await reader.cancel(); throw new ApiError('Przekroczony limit rozmiaru danych.', 413) }
    if (exact) {
      if (size > exact.length) { await reader.cancel(); throw new ApiError('Rozmiar pobranego pliku nie zgadza się z nagłówkiem.', 422) }
      exact.set(value, size - value.length)
    } else chunks.push(value)
  }
  if (exact) {
    if (size !== exact.length) throw new ApiError('Pobieranie modelu zostało przerwane. Spróbuj ponownie.', 502)
    return exact.buffer
  }
  const bytes = new Uint8Array(size)
  let at = 0
  for (const chunk of chunks) { bytes.set(chunk, at); at += chunk.length }
  return bytes.buffer
}
async function jsonInput(request: Request, limit = 32000): Promise<Record<string, unknown>> {
  if (!request.headers.get('content-type')?.startsWith('application/json')) throw new ApiError('Wymagany format JSON.', 415)
  if (Number(request.headers.get('content-length')) > limit) throw new ApiError('Przekroczony limit rozmiaru zlecenia.', 413)
  const value = JSON.parse(new TextDecoder().decode(await boundedBody(request.body, limit)))
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new ApiError('Wymagany obiekt JSON.')
  return value
}
async function key(env: BlenderEnv) {
  if (!env.BLENDER_SETTINGS_KEY || !/^[a-f0-9]{64}$/.test(env.BLENDER_SETTINGS_KEY)) throw new ApiError('Konfiguracja połączenia jest chwilowo niedostępna.', 503)
  const bytes = Uint8Array.from(env.BLENDER_SETTINGS_KEY.match(/../g)!, x => parseInt(x, 16))
  return crypto.subtle.importKey('raw', bytes, 'AES-GCM', false, ['encrypt', 'decrypt'])
}
export async function seal(value: string, owner: string, env: BlenderEnv) {
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const encrypted = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv, additionalData: new TextEncoder().encode(owner) }, await key(env), new TextEncoder().encode(value)))
  return JSON.stringify({ iv: Array.from(iv), data: Array.from(encrypted) })
}
async function unseal(value: string, owner: string, env: BlenderEnv) {
  const data = JSON.parse(value)
  return new TextDecoder().decode(await crypto.subtle.decrypt({ name: 'AES-GCM', iv: new Uint8Array(data.iv), additionalData: new TextEncoder().encode(owner) }, await key(env), new Uint8Array(data.data)))
}
async function remote(endpoint: string, credential: string, path: string, options: RequestInit = {}) {
  const target = validateEndpoint(endpoint) + path
  let response: Response
  try {
    // Workers rejects redirect:"error" when constructing the request. Inspect
    // redirects ourselves and never forward the credential to another address.
    response = await fetch(target, { ...options, redirect: 'manual', signal: AbortSignal.timeout(25000), headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + credential } })
  } catch {
    throw new ApiError('Strona nie otrzymała odpowiedzi z serwera Oracle. Sprawdź, czy adres tunelu jest aktualny, i spróbuj ponownie.', 502)
  }
  if (response.status >= 300 && response.status < 400) {
    await response.body?.cancel()
    throw new ApiError('Serwer zwrócił przekierowanie. Wklej bezpośredni adres HTTPS podany przez instalator.', 502)
  }
  if (!response.ok) {
    let message = 'Serwer jest niedostępny. Sprawdź połączenie w ustawieniach.'
    try { const data = JSON.parse(new TextDecoder().decode(await boundedBody(response.body, 8000))); if (typeof data.error === 'string') message = data.error.slice(0, 500) } catch { /* Do not echo HTML or secrets from upstream. */ }
    throw new ApiError(message, [404, 409, 429].includes(response.status) ? response.status : 502)
  }
  return response
}
const photoMetadata = (j: Job): PhotoMetadata[] => JSON.parse(j.reference_photos || '[]')
const publicJob = (j: Job) => ({ id: j.id, prompt: j.prompt, state: j.state, detail: j.detail, created: j.created, updated: j.updated, hasModel: !!j.artifact,
  referencePhotos: photoMetadata(j).map((photo, index) => ({ name: photo.name, view: photo.view, ...(photo.subject ? { subject: photo.subject } : {}), url: `/api/blender/jobs/${j.id}/photos/${index}` })) })
function photoDataUrl(bytes: ArrayBuffer) {
  const array = new Uint8Array(bytes), chunks: string[] = []
  for (let i = 0; i < array.length; i += 8192) chunks.push(String.fromCharCode(...array.subarray(i, i + 8192)))
  return 'data:image/jpeg;base64,' + btoa(chunks.join(''))
}

export async function blenderApi(request: Request, env: BlenderEnv): Promise<Response> {
  const url = new URL(request.url), owner = siteOwner(request, env)
  if (!owner) return reply({ error: 'Zaloguj się, aby korzystać ze swojego Blendera.' }, 401)
  if (request.method !== 'GET' && request.headers.get('origin') !== url.origin) return reply({ error: 'Niedozwolone źródło żądania.' }, 403)
  const db = env.DB
  if (!db) return reply({ error: 'Przechowywanie zleceń jest chwilowo niedostępne.' }, 503)
  try {
    const photoMatch = url.pathname.match(/^\/api\/blender\/jobs\/([a-f0-9-]{36})\/photos\/([0-3])$/)
    if (photoMatch && request.method === 'GET' && uuid.test(photoMatch[1])) {
      const job = await db.prepare('SELECT * FROM blender_jobs WHERE id=? AND owner=?').bind(photoMatch[1], owner).first<Job>()
      const index = Number(photoMatch[2])
      if (!job || !photoMetadata(job)[index] || !env.BUCKET) throw new ApiError('Nie znaleziono zdjęcia.', 404)
      const object = await env.BUCKET.get(`${owner}/${job.id}/reference-${index}.jpg`)
      if (!object) throw new ApiError('Nie znaleziono zdjęcia.', 404)
      return new Response(object.body, { headers: { 'Content-Type': 'image/jpeg', 'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff', 'Content-Disposition': `inline; filename="reference-${index + 1}.jpg"` } })
    }
    const connection = await db.prepare('SELECT owner,endpoint,credential FROM blender_connections WHERE owner=?').bind(owner).first<Connection>()
    const token = connection ? await unseal(connection.credential, owner, env) : ''
    if (url.pathname === '/api/blender/connection') {
      if (request.method === 'GET') {
        if (!connection) return reply({ connected: false, ready: false, detail: 'Połącz swój serwer, aby generować modele z opisu.' })
        try {
          const state = await (await remote(connection.endpoint, token, '/v1/health')).json() as { ready: boolean; model: string; detail: string; provider?: string; connectorVersion?: number; photoInput?: boolean; sceneReplay?: boolean; rendererRevision?: number; portraitRevision?: number; characterStandard?: number; coutureRevision?: number; promptMaxLength?: number; referenceQualityRevision?: number }
          // Operational capability diagnostics only: no identity, address, prompt,
          // model-supplied detail, photo, pairing token or API key enters logs.
          console.info('FROGE_ORACLE_HEALTH', JSON.stringify({ connectorVersion: Number.isInteger(state.connectorVersion) ? state.connectorVersion : 1,
            provider: state.provider === 'openai' ? 'openai' : 'ollama', ready: state.ready === true, photoInput: supportsPhotoGeneration(state), rendererRevision: Number.isInteger(state.rendererRevision) ? state.rendererRevision : 1, portraitRevision: Number.isInteger(state.portraitRevision) ? state.portraitRevision : 0, characterStandard: Number.isInteger(state.characterStandard) ? state.characterStandard : 0, coutureRevision: Number.isInteger(state.coutureRevision) ? state.coutureRevision : 0, promptMaxLength: state.promptMaxLength === 5000 ? 5000 : 2000, sceneReplay: state.sceneReplay === true }))
          return reply({ connected: true, ready: state.ready === true, model: state.model, endpoint: connection.endpoint, detail: state.detail,
            provider: state.provider === 'openai' ? 'openai' : 'ollama', connectorVersion: state.connectorVersion || 1, photoInput: supportsPhotoGeneration(state), portraitRevision: Number.isInteger(state.portraitRevision) ? state.portraitRevision : 0, characterStandard: Number.isInteger(state.characterStandard) ? state.characterStandard : 0, coutureRevision: Number.isInteger(state.coutureRevision) ? state.coutureRevision : 0, promptMaxLength: state.promptMaxLength === 5000 ? 5000 : 2000, sceneReplay: state.sceneReplay === true, referenceQualityRevision: state.referenceQualityRevision === 1 ? 1 : 0, rendererRevision: Number.isInteger(state.rendererRevision) ? state.rendererRevision : 1 })
        } catch { return reply({ connected: true, ready: false, endpoint: connection.endpoint, detail: 'Brak łączności z serwerem. Jeśli tunel został uruchomiony ponownie, wpisz nowy adres i kod połączenia.' }) }
      }
      if (request.method === 'POST') {
        const input = await jsonInput(request), endpoint = validateEndpoint(input.endpoint)
        if (typeof input.code !== 'string' || !/^[a-f0-9]{32}$/.test(input.code.trim())) throw new ApiError('Wklej cały 32-znakowy kod połączenia z instalatora.')
        // Validate encryption before exchanging a pairing code. Never expose the API token to the browser.
        await key(env)
        const response = await remote(endpoint, input.code.trim(), '/v1/pair', { method: 'POST', body: JSON.stringify({ client: owner }) })
        const paired = await response.json() as { token?: string }
        if (!paired.token || !/^[A-Za-z0-9_-]{40,100}$/.test(paired.token)) throw new ApiError('Serwer zwrócił nieprawidłowe dane połączenia.', 502)
        await db.prepare('INSERT INTO blender_connections (owner,endpoint,credential,updated) VALUES (?,?,?,?) ON CONFLICT(owner) DO UPDATE SET endpoint=excluded.endpoint,credential=excluded.credential,updated=excluded.updated').bind(owner, endpoint, await seal(paired.token, owner, env), new Date().toISOString()).run()
        return reply({ connected: true })
      }
      throw new ApiError('Niedozwolona metoda.', 405)
    }
    if (url.pathname === '/api/blender/ai') {
      if (request.method !== 'POST') throw new ApiError('Niedozwolona metoda.', 405)
      if (!connection) throw new ApiError('Najpierw połącz serwer Blendera.', 409)
      const input = await jsonInput(request)
      if (input.provider !== 'openai' && input.provider !== 'ollama') throw new ApiError('Wybierz dostawcę AI.')
      if (input.apiKey !== undefined && (typeof input.apiKey !== 'string' || !/^sk-[A-Za-z0-9_-]{20,500}$/.test(input.apiKey))) throw new ApiError('Wklej pełny klucz API OpenAI zaczynający się od sk-.')
      try {
        // No credentials are returned, logged, or persisted in browser storage/D1.
        // The existing paired worker stores this key outside the Blender container.
        const response = await remote(connection.endpoint, token, '/v1/ai', { method: 'POST', body: JSON.stringify({ provider: input.provider, ...(input.provider === 'openai' && input.apiKey ? { apiKey: input.apiKey } : {}) }) })
        await response.body?.cancel()
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) throw new ApiError('Zainstaluj aktualizację froge-oracle-openai.zip na Oracle, a następnie podłącz OpenAI.', 409)
        throw error
      }
      return reply({ saved: true })
    }
    if (url.pathname === '/api/blender/jobs') {
      if (request.method === 'GET') {
        const rows = await db.prepare('SELECT * FROM blender_jobs WHERE owner=? ORDER BY created DESC LIMIT 10').bind(owner).all<Job>()
        return reply({ jobs: rows.results.map(publicJob) })
      }
      if (request.method !== 'POST') throw new ApiError('Niedozwolona metoda.', 405)
      if (!connection) throw new ApiError('Najpierw połącz serwer Blendera.', 409)
      const input = await jsonInput(request, MAX_PHOTO_REQUEST_BYTES)
      if (typeof input.id !== 'string' || !uuid.test(input.id) || typeof input.prompt !== 'string' || !input.prompt.trim() || input.prompt.length > 5000) throw new ApiError('Wpisz opis od 1 do 5000 znaków.')
      if (input.referenceJobId !== undefined && (typeof input.referenceJobId !== 'string' || !uuid.test(input.referenceJobId) || input.referenceJobId === input.id || input.photos !== undefined || input.sourceJobId !== undefined)) throw new ApiError('Nieprawidłowe źródło zdjęć.')
      if (input.sourceJobId !== undefined && input.photos !== undefined) throw new ApiError('Do wykonania zapisanego skryptu nie można dodawać nowych zdjęć.')
      let replaySource: Job | null = null
      if (input.sourceJobId !== undefined) {
        if (typeof input.sourceJobId !== 'string' || !uuid.test(input.sourceJobId) || input.sourceJobId === input.id) throw new ApiError('Nieprawidłowe zlecenie źródłowe.')
        replaySource = await db.prepare('SELECT * FROM blender_jobs WHERE id=? AND owner=?').bind(input.sourceJobId, owner).first<Job>()
        if (!replaySource || replaySource.state !== 'failed' || replaySource.endpoint !== connection.endpoint || replaySource.prompt !== input.prompt.trim()) throw new ApiError('Nie znaleziono pasującego nieudanego zlecenia.', 409)
        const state = await (await remote(connection.endpoint, token, '/v1/health')).json() as { connectorVersion?: number; sceneReplay?: boolean }
        if ((state.connectorVersion || 1) < 5) throw new ApiError('Najpierw zainstaluj aktualizację froge-oracle-rebuild.zip na Oracle.', 409)
        if ((photoMetadata(replaySource).length || replaySource.detail.includes('Use at most 8 materials and 8 images')) && state.sceneReplay !== true) throw new ApiError('Najpierw uruchom poprawkę froge-napraw-tekstury.py na Oracle, potem sprawdź połączenie.', 409)
      }
      let photoInput = input.photos
      if (input.referenceJobId || (replaySource && photoMetadata(replaySource).length)) {
        const source = replaySource || await db.prepare('SELECT * FROM blender_jobs WHERE id=? AND owner=?').bind(input.referenceJobId, owner).first<Job>()
        if (!source || !photoMetadata(source).length || !env.BUCKET) throw new ApiError('Nie znaleziono zdjęć źródłowego zlecenia. Dodaj je ponownie.', 409)
        const entries = []
        for (const [index, photo] of photoMetadata(source).entries()) {
          const object = await env.BUCKET.get(`${owner}/${source.id}/reference-${index}.jpg`)
          if (!object) throw new ApiError('Brakuje zdjęcia źródłowego. Dodaj je ponownie.', 409)
          entries.push({ ...(photo.textureMaxSize ? { textureMaxSize: photo.textureMaxSize } : {}), name: photo.name, view: photo.view, ...(photo.subject ? { subject: photo.subject } : {}), ...(photo.faceLandmarks ? { faceLandmarks: photo.faceLandmarks } : {}), dataUrl: photoDataUrl(await boundedBody(object.body, MAX_REFERENCE_BYTES)) })
        }
        photoInput = entries
      }
      let photos: Awaited<ReturnType<typeof decodePhotoInputs>>
      try { photos = await decodePhotoInputs(photoInput) } catch (error) { throw new ApiError((error as Error).message, 422) }
      const references = JSON.stringify(photos.map(photo => photo.metadata))
      const existing = await db.prepare('SELECT * FROM blender_jobs WHERE id=? AND owner=?').bind(input.id, owner).first<Job>()
      if (existing) {
        if (existing.prompt !== input.prompt.trim() || (existing.reference_photos || '[]') !== references) throw new ApiError('Identyfikator dotyczy innego opisu lub innych zdjęć.', 409)
        return reply({ job: publicJob(existing) })
      }
      const capabilities = await (await remote(connection.endpoint, token, '/v1/health')).json() as { connectorVersion?: number; photoInput?: boolean; provider?: string; portraitRevision?: number; characterStandard?: number; coutureRevision?: number; promptMaxLength?: number; faceFitRevision?: number; referenceQualityRevision?: number }
      if (photos.some(p => p.input.textureMaxSize) && capabilities.referenceQualityRevision !== 1) throw new ApiError('Referencje 4K/8K wymagają aktualizacji generatora z obsługą jakości referencji. Zlecenie nie zostało wysłane do AI.', 409)
      if (photos.some(p => p.input.faceLandmarks) && capabilities.faceFitRevision !== 1) throw new ApiError('Dopasowanie twarzy ze zdjęcia wymaga aktualizacji Oracle z modułem pomiarów twarzy.', 409)
      if (!supportsGeneration(capabilities.connectorVersion)) throw new ApiError('Zainstaluj aktualizację froge-oracle-update.zip (v14) na Oracle. Ta wersja serwera nie obsługuje obecnego generatora.', 409)
      if (photos.length && !input.sourceJobId && !supportsPhotoGeneration(capabilities)) throw new ApiError('Zdjęcia wymagają aktualizacji generatora na Oracle do wersji 14 i wybranego OpenAI API. Zdjęcia nie zostały wysłane do AI.', 409)
      if (requiresPortraitQuality(input.prompt, photos.length) && !supportsPortraitQuality(capabilities)) throw new ApiError(PORTRAIT_UPDATE_REASON, 409)
      if (requiresCoutureQuality(input.prompt) && !supportsCoutureQuality(capabilities)) throw new ApiError(COUTURE_UPDATE_REASON, 409)
      if (input.prompt.length > 2000 && capabilities.promptMaxLength !== 5000) throw new ApiError('Opis powyżej 2000 znaków wymaga aktualizacji Oracle do v19.', 409)
      if (photos.length && !env.BUCKET) throw new ApiError('Przechowywanie zdjęć jest chwilowo niedostępne.', 503)
      const now = new Date().toISOString()
      const created = await db.prepare('INSERT INTO blender_jobs (id,owner,endpoint,prompt,state,detail,created,updated,reference_photos) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING').bind(input.id, owner, connection.endpoint, input.prompt.trim(), 'submitting', photos.length ? 'Zapisuję zdjęcia i opis…' : 'Wysyłanie opisu do serwera…', now, now, references).run()
      if (created.meta.changes !== 1) throw new ApiError('Identyfikator zlecenia jest już zajęty.', 409)
      try {
        for (const [index, photo] of photos.entries()) await env.BUCKET!.put(`${owner}/${input.id}/reference-${index}.jpg`, photo.bytes, { httpMetadata: { contentType: 'image/jpeg' } })
      } catch {
        await db.prepare('UPDATE blender_jobs SET state=?,detail=? WHERE id=? AND owner=?').bind('failed', 'Nie udało się zapisać wszystkich zdjęć. Dodaj je ponownie.', input.id, owner).run()
        throw new ApiError('Nie udało się zapisać zdjęć. Zlecenie nie zostało wysłane do AI; zachowaj formularz i spróbuj ponownie.', 503)
      }
      try {
        await remote(connection.endpoint, token, '/v1/jobs', { method: 'POST', body: JSON.stringify({ id: input.id, prompt: input.prompt.trim(), ...(input.sourceJobId ? { sourceJobId: input.sourceJobId } : {}), ...(photos.length && !input.sourceJobId ? { photos: photos.map(photo => photo.input) } : {}) }) })
        await db.prepare('UPDATE blender_jobs SET state=?,detail=? WHERE id=? AND owner=? AND state=?').bind('queued', input.sourceJobId ? 'Wykonuję zapisany plan bez nowego zapytania do AI…' : photos.length ? 'Zdjęcia i opis przyjęte. Oczekiwanie na analizę AI…' : 'Opis przyjęty. Oczekiwanie na AI…', input.id, owner, 'submitting').run()
      } catch (error) {
        // The remote may have accepted a request before its HTTP response was lost.
        // Polling the same ID resolves that ambiguity and never starts a duplicate job.
        await db.prepare('UPDATE blender_jobs SET detail=? WHERE id=? AND owner=?').bind('Sprawdzam, czy serwer przyjął zlecenie…', input.id, owner).run()
        if (error instanceof ApiError && (error.status === 409 || error.status === 429)) {
          await db.prepare('UPDATE blender_jobs SET state=?,detail=? WHERE id=? AND owner=?').bind('failed', error.message, input.id, owner).run()
          throw error
        }
      }
      return reply({ job: publicJob((await db.prepare('SELECT * FROM blender_jobs WHERE id=? AND owner=?').bind(input.id, owner).first<Job>())!) }, 202)
    }
    const match = url.pathname.match(/^\/api\/blender\/jobs\/([a-f0-9-]{36})(?:\/(model|cancel))?$/)
    if (!match || !uuid.test(match[1])) throw new ApiError('Nie znaleziono zlecenia.', 404)
    const job = await db.prepare('SELECT * FROM blender_jobs WHERE id=? AND owner=?').bind(match[1], owner).first<Job>()
    if (!job) throw new ApiError('Nie znaleziono zlecenia.', 404)
    if (match[2] === 'model' && request.method === 'GET') {
      if (!job.artifact || !env.BUCKET) throw new ApiError('Model nie jest jeszcze gotowy.', 409)
      const object = await env.BUCKET.get(`${owner}/${job.artifact}`)
      if (!object) throw new ApiError('Nie znaleziono pliku modelu.', 404)
      return new Response(object.body, { headers: { 'Content-Type': 'model/gltf-binary', 'Cache-Control': 'private, no-store', 'Content-Disposition': `attachment; filename="froge-${job.id}.glb"`, 'X-Content-Type-Options': 'nosniff' } })
    }
    if (!connection) throw new ApiError('Połącz ponownie serwer Blendera.', 409)
    // New tunnel addresses may change; the credential still identifies the same private worker.
    if (match[2] === 'cancel' && request.method === 'POST') {
      await remote(connection.endpoint, token, `/v1/jobs/${job.id}/cancel`, { method: 'POST', body: '{}' })
      await db.prepare('UPDATE blender_jobs SET state=?,detail=?,updated=? WHERE id=? AND owner=? AND state NOT IN (?,?)').bind('cancelled', 'Zlecenie anulowane.', new Date().toISOString(), job.id, owner, 'succeeded', 'failed').run()
      return reply({ cancelled: true })
    }
    if (match[2] || request.method !== 'GET') throw new ApiError('Niedozwolona metoda.', 405)
    if (['succeeded', 'failed', 'cancelled'].includes(job.state)) return reply({ job: publicJob(job) })
    let response: Response
    try { response = await remote(connection.endpoint, token, `/v1/jobs/${job.id}`) }
    catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        // A concurrent status request can overtake submission/storage. Give the
        // same identifier time to be accepted before calling it missing.
        if (job.state === 'submitting' && Date.now() - Date.parse(job.created) < 90000)
          return reply({ job: publicJob({ ...job, detail: 'Czekam na potwierdzenie przyjęcia tego zlecenia…' }) })
        job.state = 'failed'; job.detail = 'Serwer nie przyjął tego zlecenia. Opis i zdjęcia są zachowane; możesz ponowić generowanie.'; job.updated = new Date().toISOString()
        await db.prepare('UPDATE blender_jobs SET state=?,detail=?,updated=? WHERE id=? AND owner=?').bind(job.state, job.detail, job.updated, job.id, owner).run()
        return reply({ job: publicJob(job) })
      }
      throw error
    }
    const state = await response.json() as { state?: string; detail?: string }
    if (!state.state || !['queued', 'generating', 'building', 'retrying', 'succeeded', 'failed', 'cancelled'].includes(state.state)) throw new ApiError('Nieprawidłowy status z serwera.', 502)
    let artifact = job.artifact
    if (state.state === 'succeeded' && !artifact) {
      if (!env.BUCKET) throw new ApiError('Zapis modelu jest chwilowo niedostępny.', 503)
      const model = await remote(connection.endpoint, token, `/v1/jobs/${job.id}/model`)
      try {
        if (Number(model.headers.get('content-length')) > maxGlb) throw new ApiError('Wygenerowany model przekracza limit 48 MB. Wygeneruj postacie osobno.', 413)
        const bytes = await boundedBody(model.body, maxGlb, Number(model.headers.get('content-length')))
        const h = new DataView(bytes)
        if (bytes.byteLength < 20 || h.getUint32(0, true) !== 0x46546c67 || h.getUint32(4, true) !== 2 || h.getUint32(8, true) !== bytes.byteLength) throw new ApiError('Serwer zwrócił nieprawidłowy plik GLB.', 422)
        artifact = `${job.id}.glb`
        await env.BUCKET.put(`${owner}/${artifact}`, bytes)
      } catch (error) {
        if (!(error instanceof ApiError) || ![413, 422].includes(error.status)) throw error
        state.state = 'failed'; state.detail = error.message
      }
    }
    job.state = state.state; job.detail = (state.detail || '').slice(0, 600); job.artifact = artifact; job.updated = new Date().toISOString()
    await db.prepare('UPDATE blender_jobs SET state=?,detail=?,artifact=?,updated=? WHERE id=? AND owner=? AND state NOT IN (?,?)').bind(job.state, job.detail, artifact, job.updated, job.id, owner, 'cancelled', 'succeeded').run()
    return reply({ job: publicJob((await db.prepare('SELECT * FROM blender_jobs WHERE id=? AND owner=?').bind(job.id, owner).first<Job>())!) })
  } catch (error) {
    if (error instanceof ApiError) return reply({ error: error.message }, error.status)
    if (error instanceof SyntaxError) return reply({ error: 'Nieprawidłowy format danych.' }, 400)
    const message = error instanceof Error ? error.message : ''
    const storage = /D1|SQLITE|database|R2|bucket|storage/i.test(message)
    // Classify the failure without logging prompts, photos, credentials or the
    // raw exception (upstream errors can contain private request data).
    console.error('FROGE_REQUEST_FAILED', JSON.stringify({ route: url.pathname.replace(/[a-f0-9-]{36}/g, ':job'), method: request.method, category: storage ? 'storage' : 'unexpected', errorType: error instanceof Error ? error.name : 'unknown' }))
    return reply({ error: storage ? 'Zapis lub odczyt danych jest chwilowo niedostępny. Zachowaj formularz i spróbuj ponownie; sprawdzimy to samo zlecenie.' : 'Nie udało się potwierdzić zlecenia. Opis i zdjęcia pozostają w formularzu. Spróbuj ponownie — sprawdzimy ten sam model.' }, 503)
  }
}
