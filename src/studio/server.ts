// Cloudflare Worker. Provider credentials never enter generated assets or logs.
type Environment = { ASSETS: { fetch: (request: Request) => Promise<Response> }; MESHY_API_KEY?: string }
const ROOT = 'https://api.meshy.ai/openapi'
const ID = /^[a-zA-Z0-9-]{8,80}$/
const json = (data: unknown, status = 200) => Response.json(data, { status, headers: { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' } })
function failure(status: number) {
  const messages: Record<number, string> = { 401: 'Klucz Meshy jest nieprawidłowy. Sprawdź połączenie.', 402: 'Brak kredytów API Meshy. Doładuj konto API, aby wygenerować model.', 403: 'Konto Meshy nie ma dostępu do tej operacji.', 404: 'Nie znaleziono zadania. Sprawdź konto i identyfikator.', 429: 'Meshy ma teraz zbyt wiele zadań. Spróbuj ponownie za chwilę.' }
  return json({ error: messages[status] ?? 'Meshy nie przyjęło żądania. Spróbuj ponownie lub sprawdź zadanie na koncie Meshy.' }, status >= 400 && status < 600 ? status : 502)
}
export default {
  async fetch(request: Request, env: Environment): Promise<Response> {
    const url = new URL(request.url), path = url.pathname
    if (!path.startsWith('/api/3d/')) {
      const asset = await env.ASSETS.fetch(request)
      if (asset.status === 404 && request.method === 'GET' && request.headers.get('accept')?.includes('text/html')) return env.ASSETS.fetch(new Request(new URL('/index.html', url), request))
      return asset
    }
    // Keep a server-configured account restricted to the same private Site.
    if (request.headers.get('origin') && request.headers.get('origin') !== url.origin) return json({ error: 'Niedozwolone źródło żądania.' }, 403)
    if (request.method === 'GET' && path === '/api/3d/config') return json({ configured: Boolean(env.MESHY_API_KEY) })
    const key = request.headers.get('x-meshy-key')?.trim() || env.MESHY_API_KEY?.trim()
    if (!key) return json({ error: 'Podłącz Meshy w panelu „Połączenie AI”. Wymiary nie są wymagane.', code: 'NOT_CONFIGURED' }, 503)
    if (key.length > 512 || /[\r\n]/.test(key)) return json({ error: 'Nieprawidłowy klucz.' }, 400)
    const upstream = async (path: string, body?: unknown) => fetch(ROOT + path, { method: body ? 'POST' : 'GET', headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(25000), redirect: 'error' })
    try {
      if (request.method === 'GET' && path === '/api/3d/verify') {
        const response = await upstream('/v1/balance')
        return response.ok ? json({ connected: true }) : failure(response.status)
      }
      if (request.method === 'POST' && path === '/api/3d/tasks') {
        if (!request.headers.get('content-type')?.includes('application/json')) return json({ error: 'Wymagany JSON.' }, 415)
        const reader = request.body?.getReader(); let size = 0, text = ''; const decoder = new TextDecoder()
        if (!reader) return json({ error: 'Brak polecenia.' }, 400)
        while (true) { const chunk = await reader.read(); if (chunk.done) break; size += chunk.value.byteLength; if (size > 6000) { await reader.cancel(); return json({ error: 'Polecenie jest zbyt długie.' }, 413) }; text += decoder.decode(chunk.value, { stream: true }) }
        text += decoder.decode()
        let data: { action?: string; prompt?: unknown; id?: string }
        try { data = JSON.parse(text) } catch { return json({ error: 'Nieprawidłowe polecenie.' }, 400) }
        if (!data || typeof data !== 'object' || typeof data.prompt !== 'string' || !data.prompt.trim() || data.prompt.length > 800) return json({ error: 'Wpisz opis od 1 do 800 znaków. Wymiary są opcjonalne.' }, 400)
        let body: unknown
        if (data.action === 'preview') body = { mode: 'preview', prompt: data.prompt.trim(), ai_model: 'meshy-6', should_remesh: true, target_polycount: 30000, target_formats: ['glb'] }
        else if (data.action === 'refine' && typeof data.id === 'string' && ID.test(data.id)) {
          const preview = await upstream('/v2/text-to-3d/' + data.id)
          if (!preview.ok) return failure(preview.status)
          const task = await preview.json() as { status?: string; type?: string }
          if (task.status !== 'SUCCEEDED' || task.type !== 'text-to-3d-preview') return json({ error: 'Geometria musi być gotowa przed teksturowaniem.' }, 409)
          body = { mode: 'refine', preview_task_id: data.id, texture_prompt: data.prompt.trim(), enable_pbr: true, texture_resolution: '2k', target_formats: ['glb'] }
        } else return json({ error: 'Nieprawidłowa operacja.' }, 400)
        const response = await upstream('/v2/text-to-3d', body)
        if (!response.ok) return failure(response.status)
        const result = await response.json() as { result?: string }
        if (!result.result || !ID.test(result.result)) return json({ error: 'Meshy zwróciło nieprawidłowy identyfikator.' }, 502)
        return json({ id: result.result }, 201)
      }
      const match = path.match(/^\/api\/3d\/tasks\/([a-zA-Z0-9-]{8,80})(\/model)?$/)
      if (request.method === 'GET' && match) {
        const response = await upstream('/v2/text-to-3d/' + match[1])
        if (!response.ok) return failure(response.status)
        const task = await response.json() as { status: string; progress: number; model_urls?: { glb?: string } }
        if (!match[2]) return json({ id: match[1], status: task.status, progress: Math.max(0, Math.min(100, Number(task.progress) || 0)), hasModel: task.status === 'SUCCEEDED' && Boolean(task.model_urls?.glb) })
        if (task.status !== 'SUCCEEDED' || !task.model_urls?.glb) return json({ error: 'Plik modelu nie jest jeszcze gotowy.' }, 409)
        const modelUrl = new URL(task.model_urls.glb)
        if (modelUrl.protocol !== 'https:' || !(modelUrl.hostname === 'assets.meshy.ai' || modelUrl.hostname === 'cdn.meshy.ai')) return json({ error: 'Nieprawidłowy adres pliku Meshy.' }, 502)
        const model = await fetch(modelUrl, { redirect: 'error', signal: AbortSignal.timeout(60000) })
        if (!model.ok) return json({ error: 'Nie udało się pobrać modelu. Ponów pobieranie.' }, 502)
        if (Number(model.headers.get('content-length')) > 64 * 1024 * 1024) return json({ error: 'Model przekracza limit 64 MB tego podglądu.' }, 413)
        return new Response(model.body, { headers: { 'Content-Type': 'model/gltf-binary', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' } })
      }
      return json({ error: 'Nieznana operacja.' }, 404)
    } catch { return json({ error: request.method === 'POST' ? 'Nie otrzymano potwierdzenia z Meshy. Zadanie mogło powstać — sprawdź konto Meshy przed ponowną generacją, aby uniknąć podwójnego kosztu.' : 'Nie udało się połączyć z Meshy. Ponów sprawdzanie istniejącego zadania; nie musisz generować go od nowa.' }, 502) }
  },
}
