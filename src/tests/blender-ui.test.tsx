import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { RemoteGenerator } from '../blender/RemoteGenerator'
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

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
    if (path.endsWith('/connection')) return Response.json({ connected: true, ready: true })
    if (path.endsWith('/model')) return new Response(new Uint8Array([1, 2, 3]), { headers: { 'Content-Type': 'model/gltf-binary' } })
    if (path.endsWith('/jobs') && init?.method === 'POST') return Response.json({ job })
    if (path.endsWith('/jobs')) return Response.json({ jobs: [] })
    return Response.json({ job: { ...job, state, detail: state === 'failed' ? 'AI nie ukończyło modelu' : 'ready', hasModel: state === 'succeeded' } })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt={prompt} onStart={() => 7} onResult={onResult}/>)
  await screen.findByText('AI + Blender gotowe')
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
    if (path.endsWith('/connection')) return Response.json({ connected: true, ready: true })
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
  await screen.findByText('AI + Blender gotowe')
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
