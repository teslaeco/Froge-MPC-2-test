import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { RemoteGenerator } from '../blender/RemoteGenerator'
import { DEFAULT_PHOTO_PROMPT } from '../blender/photoReferences'

// Browser decoding is separate from this interaction/HTTP contract test.
vi.mock('../blender/photoReferences', async importOriginal => ({
  ...await importOriginal<object>(),
  prepareReferencePhoto: vi.fn(async (file: File) => ({ name: file.name, view: 'other', dataUrl: 'data:image/jpeg;base64,fixture' })),
}))
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

function mount(version = 15, provider = 'openai', history: object[] = []) {
  const fetcher = vi.fn(async (url, init) => {
    const path = String(url)
    if (path.endsWith('/connection')) return Response.json({ connected: true, ready: true, connectorVersion: version, portraitRevision: version>=15 ? 1 : 0, provider, photoInput: true })
    if (init?.method === 'POST') return Response.json({ job: { ...JSON.parse(init.body), state: 'failed', detail: 'Test completed', hasModel: false } })
    return Response.json(path.endsWith('/jobs') ? { jobs: history } : { job: history[0] })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt="" onStart={() => 1} onResult={vi.fn()}/>)
  return fetcher
}
function choose(names: string[]) {
  fireEvent.change(screen.getByLabelText('Dodaj zdjęcia · JPG, PNG, WebP'), { target: { files: names.map(name => new File(['fixture'], name, { type: 'image/jpeg' })) } })
}

it('previews, labels and removes photos without submitting; photo-only generation sends selected bytes', async () => {
  const fetcher = mount()
  choose(['front.jpg', 'profile.jpg'])
  await screen.findByAltText('Zdjęcie referencyjne 2: profile.jpg')
  fireEvent.change(screen.getByLabelText('Ujęcie 2'), { target: { value: 'side' } })
  fireEvent.click(screen.getByRole('button', { name: 'Usuń zdjęcie 1' }))
  expect(screen.getByLabelText('Ujęcie 1')).toHaveValue('side')
  expect(fetcher.mock.calls.some(([, init]) => init?.method === 'POST')).toBe(false)
  const button = screen.getByRole('button', { name: 'Generuj model 3D ze zdjęć' })
  await waitFor(() => expect(button).toBeEnabled())
  fireEvent.click(button)
  await waitFor(() => expect(fetcher.mock.calls.some(([, init]) => init?.method === 'POST')).toBe(true))
  const sent = JSON.parse(fetcher.mock.calls.find(([, init]) => init?.method === 'POST')![1].body)
  expect(sent).toMatchObject({ prompt: DEFAULT_PHOTO_PROMPT, photos: [{ name: 'profile.jpg', view: 'side', dataUrl: 'data:image/jpeg;base64,fixture' }] })
})

it.each([[13, 'openai'], [14, 'ollama']] as const)('blocks photo submission on worker %i with %s', async (version, provider) => {
  const fetcher = mount(version, provider)
  choose(['front.jpg'])
  await screen.findByAltText('Zdjęcie referencyjne 1: front.jpg')
  expect(screen.getByRole('button', { name: 'Generuj model 3D ze zdjęć' })).toBeDisabled()
  expect(fetcher.mock.calls.some(([, init]) => init?.method === 'POST')).toBe(false)
})

it('rejects more than four photos and retries the original saved references after reload', async () => {
  const original = { id: '12345678-1234-4234-8234-123456789abc', prompt: 'Model ze zdjęcia', state: 'failed', detail: 'timeout', hasModel: false, referencePhotos: [{ name: 'front.jpg', view: 'front', url: '/api/blender/jobs/12345678-1234-4234-8234-123456789abc/photos/0' }] }
  const fetcher = mount(15, 'openai', [original])
  choose(['1.jpg', '2.jpg', '3.jpg', '4.jpg', '5.jpg'])
  await screen.findByText('Możesz dołączyć maksymalnie 4 zdjęcia. Usuń jedno, aby dodać kolejne.')
  expect(screen.queryByAltText('Zdjęcie referencyjne 1: 1.jpg')).not.toBeInTheDocument()
  const button = await screen.findByRole('button', { name: 'Generuj ponownie z tych zdjęć · OpenAI API' })
  await waitFor(() => expect(button).toBeEnabled())
  expect(screen.getByAltText('Referencja 1: front.jpg')).toHaveAttribute('src', original.referencePhotos[0].url)
  fireEvent.click(button)
  await waitFor(() => expect(fetcher.mock.calls.some(([, init]) => init?.method === 'POST')).toBe(true))
  const sent = JSON.parse(fetcher.mock.calls.find(([, init]) => init?.method === 'POST')![1].body)
  expect(sent).toMatchObject({ prompt: original.prompt, referenceJobId: original.id })
  expect(sent).not.toHaveProperty('photos')
  expect(sent.id).not.toBe(original.id)
})
