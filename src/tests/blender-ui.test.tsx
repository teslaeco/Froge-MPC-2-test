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
