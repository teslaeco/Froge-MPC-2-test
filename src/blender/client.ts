export type GenerationJob = { id: string; prompt: string; state: string; detail: string; created: string; updated: string; hasModel: boolean }
export type BlenderConnection = { connected: boolean; ready: boolean; endpoint?: string; model?: string; detail: string; provider?: 'ollama' | 'openai'; connectorVersion?: number }
export const finished = (job: GenerationJob) => ['succeeded', 'failed', 'cancelled'].includes(job.state)
export class BlenderRequestError extends Error {
  readonly retryable: boolean
  readonly status: number
  constructor(message: string, retryable = false, status = 0) { super(message); this.retryable = retryable; this.status = status }
}
async function receive<T>(path: string, options: RequestInit | undefined, read: (response: Response) => Promise<T>): Promise<T> {
  const controller = new AbortController()
  const abort = () => controller.abort()
  if (options?.signal?.aborted) abort()
  else options?.signal?.addEventListener('abort', abort, { once: true })
  // Include reading the body in the deadline; a stalled mobile connection must
  // not prevent the next status poll indefinitely. Never repeat a POST here.
  const timer = setTimeout(abort, 60000)
  try {
    const response = await fetch('/api/blender/' + path, { ...options, cache: 'no-store', signal: controller.signal })
    if (response.status === 401 || response.status === 403) throw new BlenderRequestError('Odśwież stronę i zaloguj się ponownie do Froge.', false, response.status)
    return await read(response)
  } catch (error) {
    if (error instanceof BlenderRequestError) throw error
    if (controller.signal.aborted) throw new BlenderRequestError('Nie otrzymałem odpowiedzi na czas. Sprawdź połączenie z internetem.', true)
    if (error instanceof TypeError) throw new BlenderRequestError('Nie udało się pobrać danych. Sprawdź połączenie z internetem.', true)
    throw new BlenderRequestError('Nie udało się odczytać odpowiedzi serwera. Odśwież stronę.', true)
  } finally {
    clearTimeout(timer)
    options?.signal?.removeEventListener('abort', abort)
  }
}
export async function blenderRequest<T>(path: string, options?: RequestInit): Promise<T> {
  return receive(path, options, async response => {
    if (!response.headers.get('content-type')?.includes('application/json')) throw new BlenderRequestError('Nie można odczytać odpowiedzi. Odśwież stronę i zaloguj się ponownie do Froge.', response.status >= 500, response.status)
    const data = await response.json()
    if (!response.ok) throw new BlenderRequestError(data.error || 'Operacja nie powiodła się.', response.status >= 500 || response.status === 429, response.status)
    return data as T
  })
}
export async function generatedModel(id: string, options?: RequestInit) {
  return receive(`jobs/${id}/model`, options, async response => {
    if (!response.ok || !response.headers.get('content-type')?.includes('model/gltf-binary')) {
      let message = 'Nie udało się pobrać gotowego modelu.'
      try { message = (await response.json()).error || message } catch { /* Preserve a useful error. */ }
      throw new BlenderRequestError(message, response.status >= 500 || response.status === 429, response.status)
    }
    return response.arrayBuffer()
  })
}
