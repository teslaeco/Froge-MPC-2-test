export type GenerationJob = { id: string; prompt: string; state: string; detail: string; created: string; updated: string; hasModel: boolean }
export type BlenderConnection = { connected: boolean; ready: boolean; endpoint?: string; model?: string; detail: string }
export const finished = (job: GenerationJob) => ['succeeded', 'failed', 'cancelled'].includes(job.state)
export async function blenderRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch('/api/blender/' + path, options)
  if (!response.headers.get('content-type')?.includes('application/json')) throw new Error('Nie można odczytać odpowiedzi. Zaloguj się ponownie do Froge.')
  const data = await response.json()
  if (!response.ok) throw new Error(data.error || 'Operacja nie powiodła się.')
  return data as T
}
export async function generatedModel(id: string) {
  const response = await fetch(`/api/blender/jobs/${id}/model`)
  if (!response.ok || !response.headers.get('content-type')?.includes('model/gltf-binary')) {
    let message = 'Nie udało się pobrać gotowego modelu.'
    try { message = (await response.json()).error || message } catch { /* Preserve a useful error. */ }
    throw new Error(message)
  }
  return response.arrayBuffer()
}
