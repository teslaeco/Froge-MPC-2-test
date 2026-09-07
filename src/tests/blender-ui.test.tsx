import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { RemoteGenerator } from '../blender/RemoteGenerator'
import { blenderRequest } from '../blender/client'
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.useRealTimers() })

it('recovers the same job after a lost mobile connection without starting another generation', async () => {
  const job = { id: '12345678-1234-4234-8234-123456789abc', prompt: 'Dąb z 20 lampkami', state: 'generating', detail: 'AI projektuje scenę: 205 znaków. Ostatnie dane 0 s temu.', hasModel: false }
  let reachable = false
  const onResult = vi.fn(async () => true)
  const fetcher = vi.fn(async (url, _init) => {
    const path = String(url)
    if (path.endsWith('/connection')) return Response.json({ connected: true, ready: true, provider: 'ollama', connectorVersion: 9 })
    if (path.endsWith('/jobs')) return Response.json({ jobs: [job] })
    if (!reachable) throw new TypeError('Failed to fetch')
    if (path.endsWith('/model')) return new Response(new Uint8Array([1, 2, 3]), { headers: { 'Content-Type': 'model/gltf-binary' } })
    return Response.json({ job: { ...job, state: 'succeeded', detail: 'Model gotowy', hasModel: true } })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt={job.prompt} onStart={() => 8} onResult={onResult}/>)
  await screen.findByText('Postęp chwilowo niedostępny')
  expect(screen.getByText(job.detail).closest('details')).not.toHaveAttribute('open')
  expect(screen.queryByText('Failed to fetch')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Podłącz Astrę' })).toBeEnabled()
  expect(screen.getByRole('button', { name: 'Generowanie w toku…' })).toBeDisabled()
  reachable = true
  fireEvent(window, new Event('online'))
  await screen.findByText('Nowy model w podglądzie')
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  expect(onResult).toHaveBeenCalledExactlyOnceWith(expect.anything(), expect.objectContaining({ id: job.id, state: 'succeeded' }), 8)
  expect(fetcher.mock.calls.every(([, init]) => !init?.method || init.method === 'GET')).toBe(true)
})

it('ends a stalled request so that status recovery can continue', async () => {
  vi.useFakeTimers()
  vi.stubGlobal('fetch', vi.fn((_url, options) => new Promise((_resolve, reject) => {
    options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
  })))
  const request = blenderRequest('connection')
  const rejected = expect(request).rejects.toMatchObject({ retryable: true, message: 'Nie otrzymałem odpowiedzi na czas. Sprawdź połączenie z internetem.' })
  await vi.advanceTimersByTimeAsync(60000)
  await rejected
})

it('asks for sign-in after an expired session instead of continually treating it as generation progress', async () => {
  const job = { id: '12345678-1234-4234-8234-123456789abc', prompt: 'Dąb', state: 'generating', detail: '', hasModel: false }
  vi.stubGlobal('fetch', vi.fn(async url => Response.json(String(url).endsWith('/connection') ? { connected: true, ready: true, connectorVersion: 9 } : String(url).endsWith('/jobs') ? { jobs: [job] } : { error: 'Authentication required' }, { status: String(url).endsWith(job.id) ? 401 : 200 })))
  render(<RemoteGenerator prompt="Dąb" onStart={() => 1} onResult={vi.fn()}/>)
  await screen.findByRole('button', { name: 'Odśwież i zaloguj się' })
  expect(screen.queryByText('Ponawiam odczyt tego samego zlecenia.')).not.toBeInTheDocument()
})

it.each([5, 6, 7, 8])('requires the geometry update on worker v%i', async version => {
  const job = { id: '12345678-1234-4234-8234-123456789abc', prompt: 'Dąb', state: 'failed', detail: '/work/generate.py cannot unpack non-iterable Object object', hasModel: false }
  vi.stubGlobal('fetch', vi.fn(async url => Response.json(String(url).endsWith('/connection') ? { connected: true, ready: true, connectorVersion: version } : String(url).endsWith('/jobs') ? { jobs: [job] } : { job })))
  render(<RemoteGenerator prompt="Dąb" onStart={() => 1} onResult={vi.fn()}/>)
  await screen.findByText('Zaktualizuj generator na Oracle')
  await screen.findByText('Nie udało się wygenerować modelu')
  expect(screen.queryByRole('button', { name: 'Wykonaj zapisany skrypt' })).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Generuj model 3D' })).toBeDisabled()
})

it('offers saved-script execution without requiring ready AI or submitting a new description', async () => {
  const original = { id: '12345678-1234-4234-8234-123456789abc', prompt: 'Dąb z lampkami', state: 'failed', detail: '/work/generate.py generated_type RGBA', hasModel: false }
  const fetcher = vi.fn(async (url, init) => {
    const path = String(url)
    if (path.endsWith('/connection')) return Response.json({ connected: true, ready: false, connectorVersion: 9 })
    if (path.endsWith('/jobs') && init?.method === 'POST') return Response.json({ job: { ...original, ...JSON.parse(init.body), state: 'failed', detail: 'fixture complete' } })
    if (path.endsWith('/jobs')) return Response.json({ jobs: [original] })
    return Response.json({ job: original })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt="" onStart={() => 1} onResult={vi.fn()}/>)
  const button = await screen.findByRole('button', { name: 'Wykonaj zapisany skrypt' })
  expect(button).toBeEnabled()
  expect(screen.getByText('Szczegóły błędu').parentElement).not.toHaveAttribute('open')
  fireEvent.click(button)
  await waitFor(() => expect(fetcher.mock.calls.some(([, init]) => init?.method === 'POST')).toBe(true))
  const sent = fetcher.mock.calls.find(([, init]) => init?.method === 'POST')!
  expect(JSON.parse(sent[1].body)).toMatchObject({ prompt: original.prompt, sourceJobId: original.id })
  expect(JSON.parse(sent[1].body).id).not.toBe(original.id)
})

it('requires the actual paired server before submitting generation', async () => {
  vi.stubGlobal('fetch', vi.fn(async url => Response.json(String(url).endsWith('/connection') ? { connected: false, ready: false } : { jobs: [] })))
  render(<RemoteGenerator prompt="Dąb" onStart={() => 1} onResult={vi.fn()}/>)
  await screen.findByText('Serwer niepołączony')
  expect(screen.getByRole('button', { name: 'Generuj model 3D' })).toBeDisabled()
  fireEvent.click(screen.getByRole('button', { name: 'Połącz serwer Blendera' }))
  expect(screen.getByLabelText('Kod połączenia')).toHaveAttribute('type', 'password')
})

it.each(['succeeded', 'failed'])('uses the real %s response and never selects a sample', async state => {
  const onResult = vi.fn(async () => true), prompt = 'Duży dąb z korą i liśćmi'
  const job = { id: '12345678-1234-4234-8234-123456789abc', prompt, state: 'queued', detail: '', hasModel: false }
  const fetcher = vi.fn(async (url, init) => {
    const path = String(url)
    if (path.endsWith('/connection')) return Response.json({ connected: true, ready: true, connectorVersion: 9 })
    if (path.endsWith('/model')) return new Response(new Uint8Array([1, 2, 3]), { headers: { 'Content-Type': 'model/gltf-binary' } })
    if (path.endsWith('/jobs') && init?.method === 'POST') return Response.json({ job })
    if (path.endsWith('/jobs')) return Response.json({ jobs: [] })
    return Response.json({ job: { ...job, state, detail: state === 'failed' ? 'AI nie ukończyło modelu' : 'ready', hasModel: state === 'succeeded' } })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt={prompt} onStart={() => 7} onResult={onResult}/>)
  await screen.findByText('Lokalny Qwen + Blender')
  fireEvent.click(screen.getByRole('button', { name: 'Generuj model 3D' }))
  await screen.findByText(state === 'succeeded' ? 'Nowy model w podglądzie' : 'Nie udało się wygenerować modelu')
  const submitted = fetcher.mock.calls.find(([, init]) => init?.method === 'POST')!
  expect(JSON.parse(submitted[1].body).prompt).toBe(prompt)
  if (state === 'succeeded') await waitFor(() => expect(onResult).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({ state }), 7))
  else expect(onResult).not.toHaveBeenCalled()
  expect(fetcher.mock.calls.every(([url]) => !String(url).includes('/models/'))).toBe(true)
})

it('retries the saved description after refresh even when the input is empty', async () => {
  const original = { id: '12345678-1234-4234-8234-123456789abc', prompt: 'Duży dąb z korą i liśćmi', state: 'failed', detail: 'timed out', hasModel: false }
  const fetcher = vi.fn(async (url, init) => {
    const path = String(url)
    if (path.endsWith('/connection')) return Response.json({ connected: true, ready: true, connectorVersion: 9 })
    if (path.endsWith('/jobs') && init?.method === 'POST') return Response.json({ job: { ...JSON.parse(init.body), state: 'queued', detail: 'Opis przyjety.', hasModel: false } })
    if (path.endsWith('/jobs')) return Response.json({ jobs: [original] })
    return Response.json({ job: original })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt="" onStart={() => 1} onResult={vi.fn()}/>)
  const retry = await screen.findByRole('button', { name: 'Ponów ten opis' })
  expect(screen.getByText('AI nie odpowiedziało w limicie czasu. Model nie został zapisany.')).toBeInTheDocument()
  fireEvent.click(retry)
  await waitFor(() => expect(fetcher.mock.calls.some(([, init]) => init?.method === 'POST')).toBe(true))
  const [, request] = fetcher.mock.calls.find(([, init]) => init?.method === 'POST')!
  expect(JSON.parse(request.body).prompt).toBe(original.prompt)
  expect(JSON.parse(request.body).id).not.toBe(original.id)
})

it('configures Astra through the owner API and clears the password field after saving', async () => {
  let provider = 'ollama'
  const apiKey = 'sk-fixture-' + 'a'.repeat(30)
  const fetcher = vi.fn(async (url, _init) => {
    const path = String(url)
    if (path.endsWith('/ai')) { provider = 'openai'; return Response.json({ saved: true }) }
    if (path.endsWith('/connection')) return Response.json({ connected: true, ready: true, provider, connectorVersion: 4, model: provider === 'openai' ? 'gpt-6-astra' : 'qwen2.5-coder:7b' })
    return Response.json({ jobs: [] })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt="Dąb z lampkami" onStart={() => 1} onResult={vi.fn()}/>)
  await screen.findByText('Lokalny Qwen + Blender')
  fireEvent.click(screen.getByRole('button', { name: 'Ustawienia serwera' }))
  const input = screen.getByLabelText('Klucz API OpenAI')
  expect(input).toHaveAttribute('type', 'password')
  fireEvent.change(input, { target: { value: apiKey } })
  fireEvent.click(screen.getByRole('button', { name: 'Podłącz OpenAI' }))
  await screen.findByText('OpenAI + Blender gotowe')
  expect(input).toHaveValue('')
  const saved = fetcher.mock.calls.find(([url]) => String(url).endsWith('/ai'))!
  expect(JSON.parse(saved[1].body)).toEqual({ provider: 'openai', apiKey })
  expect(localStorage.length).toBe(0)
})
