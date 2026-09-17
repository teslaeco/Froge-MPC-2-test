import { afterEach, expect, it, vi } from 'vitest'
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { RemoteGenerator } from '../../../src/blender/RemoteGenerator'

vi.mock('../../../src/blender/GenerationExports', () => ({ GenerationExports: () => null }))
vi.mock('../../../src/blender/GenerationReport', () => ({ GenerationReport: () => null }))
vi.mock('../../../src/studio/codexDraft', () => ({
  connectCodexExecutor: () => () => {},
  instructionsForGeneration: () => 'Zbuduj nowy model i sprawdź jego rendery.',
  regenerateCodexDraft: vi.fn(),
  setCodexAvailability: vi.fn(),
  setCodexExecution: vi.fn(),
  updateCodexContext: vi.fn(),
}))

afterEach(() => { cleanup(); vi.unstubAllGlobals() })

const previous = {
  id: '12345678-1234-4234-8234-123456789abc',
  prompt: 'Poprzednia rzeźba', state: 'succeeded', detail: 'Zapisany poprzedni wynik',
  hasModel: true, modelStatus: 'reviewed',
}
const connection = {
  connected: true, ready: true, textReady: true, provider: 'openai',
  connectorVersion: 31, instructionsRevision: 1,
}
function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>(done => { resolve = done })
  return { promise, resolve }
}
async function settle() {
  // Flush the real response body promises and React work before negative assertions.
  await new Promise(resolve => setTimeout(resolve, 0))
}

it.each(['reviewed', 'retryable-error'] as const)('ignores a late old status (%s) while the next POST is pending', async outcome => {
  const oldStatus = deferred<Response>(), submission = deferred<Response>()
  let next = { ...previous, id: '', prompt: '', state: 'queued', hasModel: false, modelStatus: 'none' }
  const onResult = vi.fn(async () => true), onJobChange = vi.fn()
  const fetcher = vi.fn((url: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const path = String(url)
    if (path.endsWith('/connection')) return Promise.resolve(Response.json(connection))
    if (path.endsWith('/jobs') && init?.method === 'POST') {
      const input = JSON.parse(String(init.body))
      next = { ...next, id: input.id, prompt: input.prompt, detail: 'Nowe zlecenie przyjęte' }
      return submission.promise
    }
    if (path.endsWith('/jobs')) return Promise.resolve(Response.json({ jobs: [previous] }))
    if (path.endsWith('/jobs/' + previous.id)) return oldStatus.promise
    if (next.id && path.endsWith('/jobs/' + next.id)) return Promise.resolve(Response.json({ job: next }))
    if (path.endsWith('/model')) return Promise.resolve(new Response(new Uint8Array([1, 2, 3]), { headers: { 'Content-Type': 'model/gltf-binary' } }))
    throw new Error('Unexpected request: ' + path)
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt="Nowy dąb" onStart={() => 1} onResult={onResult} onJobChange={onJobChange}/>)
  await waitFor(() => expect(fetcher.mock.calls.filter(([url]) => String(url).endsWith('/jobs/' + previous.id))).toHaveLength(1))
  await waitFor(() => expect(screen.getByRole('button', { name: 'Generuj model 3D' })).toBeEnabled())
  fireEvent.click(screen.getByRole('button', { name: 'Generuj model 3D' }))
  expect(screen.getByRole('button', { name: 'Wysyłam zlecenie…' })).toBeDisabled()
  expect(next.prompt).toBe('Nowy dąb')
  onJobChange.mockClear()
  await act(async () => {
    oldStatus.resolve(outcome === 'reviewed'
      ? Response.json({ job: previous })
      : Response.json({ error: 'Stary status chwilowo niedostępny.' }, { status: 503 }))
    await settle()
  })
  expect(onResult).not.toHaveBeenCalled()
  expect(onJobChange).not.toHaveBeenCalled()
  expect(fetcher.mock.calls.some(([url]) => String(url).endsWith('/model'))).toBe(false)

  // active.id has not changed yet: the old effect's online handler is still mounted.
  // It must not acquire the new serial and restart polling the previous job.
  await act(async () => { fireEvent(window, new Event('online')); await settle() })
  expect(fetcher.mock.calls.filter(([url]) => String(url).endsWith('/jobs/' + previous.id))).toHaveLength(1)
  expect(screen.getByRole('button', { name: 'Wysyłam zlecenie…' })).toBeDisabled()
  expect(fetcher.mock.calls.filter(([, init]) => init?.method === 'POST')).toHaveLength(1)

  await act(async () => { submission.resolve(Response.json({ job: next })); await settle() })
  await waitFor(() => expect(onJobChange).toHaveBeenCalledWith(expect.objectContaining({ id: next.id, prompt: 'Nowy dąb' })))
  expect(screen.getByText('Nowe zlecenie przyjęte')).toBeInTheDocument()
  expect(onResult).not.toHaveBeenCalled()
})

it('ignores an old model download that finishes during a new pending POST', async () => {
  const oldModel = deferred<Response>(), submission = deferred<Response>()
  let next = { ...previous, id: '', prompt: '', state: 'queued', hasModel: false, modelStatus: 'none' }
  const onResult = vi.fn(async () => true)
  const fetcher = vi.fn((url: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const path = String(url)
    if (path.endsWith('/connection')) return Promise.resolve(Response.json(connection))
    if (path.endsWith('/jobs') && init?.method === 'POST') {
      const input = JSON.parse(String(init.body))
      next = { ...next, id: input.id, prompt: input.prompt }
      return submission.promise
    }
    if (path.endsWith('/jobs')) return Promise.resolve(Response.json({ jobs: [previous] }))
    if (path.endsWith('/jobs/' + previous.id)) return Promise.resolve(Response.json({ job: previous }))
    if (path.endsWith('/jobs/' + previous.id + '/model')) return oldModel.promise
    if (next.id && path.endsWith('/jobs/' + next.id)) return Promise.resolve(Response.json({ job: next }))
    throw new Error('Unexpected request: ' + path)
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt="Nowy dąb" onStart={() => 1} onResult={onResult}/>)
  await waitFor(() => expect(fetcher.mock.calls.some(([url]) => String(url).endsWith('/model'))).toBe(true))
  await waitFor(() => expect(screen.getByRole('button', { name: 'Generuj model 3D' })).toBeEnabled())
  fireEvent.click(screen.getByRole('button', { name: 'Generuj model 3D' }))
  expect(screen.getByRole('button', { name: 'Wysyłam zlecenie…' })).toBeDisabled()
  await act(async () => {
    oldModel.resolve(new Response(new Uint8Array([1, 2, 3]), { headers: { 'Content-Type': 'model/gltf-binary' } }))
    await settle()
  })
  expect(onResult).not.toHaveBeenCalled()
  await act(async () => { submission.resolve(Response.json({ job: next })); await settle() })
  expect(onResult).not.toHaveBeenCalled()
  expect(fetcher.mock.calls.filter(([, init]) => init?.method === 'POST')).toHaveLength(1)
})
