export type Task = { id: string; status: string; progress: number; hasModel: boolean }
export type Job = { id: string; prompt: string; stage: 'preview' | 'refine'; textured: boolean; previewId?: string; textureRequestUncertain?: boolean }
export class ApiError extends Error { status: number; constructor(message: string, status: number) { super(message); this.status = status } }
export async function api<T>(path: string, key: string, signal?: AbortSignal, body?: unknown): Promise<T> {
  const response = await fetch('/api/3d/' + path, { method: body ? 'POST' : 'GET', headers: { ...(key ? { 'x-meshy-key': key } : {}), ...(body ? { 'Content-Type': 'application/json' } : {}) }, body: body ? JSON.stringify(body) : undefined, signal })
  if (!response.headers.get('content-type')?.includes('application/json')) throw new Error('Usługa generowania jest niedostępna. Odśwież stronę i spróbuj ponownie.')
  const data = await response.json()
  if (!response.ok) throw new ApiError(data.error || 'Nie udało się wykonać operacji.', response.status)
  return data as T
}
function delay(signal: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    if (signal.aborted) { reject(new DOMException('Aborted', 'AbortError')); return }
    const abort = () => { clearTimeout(timer); reject(new DOMException('Aborted', 'AbortError')) }
    const timer = setTimeout(() => { signal.removeEventListener('abort', abort); resolve() }, 4000)
    signal.addEventListener('abort', abort, { once: true })
  })
}
export async function followJob(initial: Job, key: string, signal: AbortSignal, onTask: (task: Task, job: Job) => void, onJob: (job: Job) => void): Promise<Job> {
  let job = initial
  for (let attempt = 0; attempt < 450; attempt++) {
    const task = await api<Task>('tasks/' + job.id, key, signal)
    onTask(task, job)
    if (['FAILED', 'CANCELED', 'EXPIRED'].includes(task.status)) throw new Error('Meshy zakończyło zadanie bez modelu (' + task.status + '). Sprawdź je na koncie Meshy lub zmień opis.')
    if (task.status === 'SUCCEEDED') {
      if (!task.hasModel) throw new Error('Zadanie zakończone, ale Meshy nie zwróciło pliku GLB.')
      if (job.stage === 'preview' && job.textured) {
        // A paid POST is never automatically retried on network errors.
        if (job.textureRequestUncertain) throw new Error('Brak potwierdzenia utworzenia tekstur. Sprawdź zadanie w Meshy przed nową generacją, aby nie naliczyć kosztu ponownie. Możesz pobrać samą geometrię.')
        job = { ...job, textureRequestUncertain: true }; onJob(job)
        let next: { id: string }
        try { next = await api<{ id: string }>('tasks', key, signal, { action: 'refine', id: job.id, prompt: job.prompt }) }
        catch (e) { if (e instanceof ApiError && [400,401,402,403,404,409,413,415,429].includes(e.status)) { job = { ...job, textureRequestUncertain: false }; onJob(job) }; throw e }
        job = { ...job, previewId: job.id, id: next.id, stage: 'refine', textureRequestUncertain: false }; onJob(job)
        continue
      }
      return job
    }
    await delay(signal)
  }
  throw new Error('Przerwano długie oczekiwanie. Zadanie jest zapisane — możesz wznowić sprawdzanie.')
}
export async function modelBytes(id: string, key: string, signal: AbortSignal) {
  const response = await fetch('/api/3d/tasks/' + id + '/model', { headers: key ? { 'x-meshy-key': key } : {}, signal })
  if (!response.ok) { const data = await response.json().catch(() => ({})); throw new Error(data.error || 'Nie udało się pobrać modelu.') }
  const reader = response.body?.getReader(); if (!reader) throw new Error('Pusty plik modelu.')
  const chunks: Uint8Array[] = []; let length = 0
  while (true) { const { done, value } = await reader.read(); if (done) break; length += value.byteLength; if (length > 64 * 1024 * 1024) { await reader.cancel(); throw new Error('Model przekracza limit 64 MB podglądu.') }; chunks.push(value) }
  const bytes = new Uint8Array(length); let offset = 0
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length }
  return bytes.buffer
}
export function savedJob(): Job | null {
  try { const j = JSON.parse(sessionStorage.getItem('froge-ai-job') || 'null'); return j && /^[a-zA-Z0-9-]{8,80}$/.test(j.id) && typeof j.prompt === 'string' && ['preview','refine'].includes(j.stage) ? j : null } catch { return null }
}
export function saveJob(job: Job) { try { sessionStorage.setItem('froge-ai-job', JSON.stringify(job)) } catch { /* Session storage may be disabled. The in-memory job remains usable. */ } }
