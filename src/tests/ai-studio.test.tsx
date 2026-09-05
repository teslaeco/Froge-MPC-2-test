import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { BoxGeometry, Group, Mesh, MeshBasicMaterial } from 'three'
import { ModelStudio } from '../components/ModelStudio'
import worker from '../studio/server'
import { followJob, type Job } from '../studio/generation'
import { exportModel, modelSize, transformModel, EMPTY_ADJUSTMENTS } from '../studio/aiModel'

afterEach(() => { cleanup(); vi.unstubAllGlobals(); sessionStorage.clear() })
const env = { ASSETS: { fetch: async () => new Response('asset') } }
const request = (body: unknown, key = 'test-key') => new Request('https://studio.test/api/3d/tasks', { method: 'POST', headers: { 'Content-Type': 'application/json', 'x-meshy-key': key, Origin: 'https://studio.test' }, body: JSON.stringify(body) })

describe('freeform 3D service boundary', () => {
  it('sends an oak description verbatim to generation with no required dimensions', async () => {
    const remote = vi.fn().mockResolvedValue(Response.json({ result: 'task-12345678' })); vi.stubGlobal('fetch', remote)
    const result = await worker.fetch(request({ action: 'preview', prompt: 'A teraz zrób drzewo dąb' }), env)
    expect(result.status).toBe(201)
    expect(await result.json()).toEqual({ id: 'task-12345678' })
    expect(JSON.parse(remote.mock.calls[0][1].body)).toMatchObject({ prompt: 'A teraz zrób drzewo dąb', mode: 'preview', target_formats: ['glb'] })
    expect(remote.mock.calls[0][1].headers.Authorization).toBe('Bearer test-key')
  })
  it('reports missing key, invalid input and insufficient credits without a fake result', async () => {
    const remote = vi.fn().mockResolvedValue(new Response('', { status: 402 })); vi.stubGlobal('fetch', remote)
    expect((await worker.fetch(request({ action: 'preview', prompt: 'dąb' }, ''), env)).status).toBe(503)
    expect((await worker.fetch(request({ action: 'preview', prompt: '' }), env)).status).toBe(400)
    expect(remote).not.toHaveBeenCalled()
    const result = await worker.fetch(request({ action: 'preview', prompt: 'dąb' }), env)
    expect(result.status).toBe(402); expect(await result.json()).toMatchObject({ error: expect.stringContaining('kredytów') })
  })
  it('blocks foreign origins and arbitrary asset URLs', async () => {
    const foreign = new Request('https://studio.test/api/3d/tasks', { method: 'POST', headers: { Origin: 'https://other.test' } })
    expect((await worker.fetch(foreign, { ...env, MESHY_API_KEY: 'secret' })).status).toBe(403)
    const remote = vi.fn().mockResolvedValue(Response.json({ status: 'SUCCEEDED', model_urls: { glb: 'https://evil.test/model.glb' } })); vi.stubGlobal('fetch', remote)
    const result = await worker.fetch(new Request('https://studio.test/api/3d/tasks/task-12345678/model'), { ...env, MESHY_API_KEY: 'secret' })
    expect(result.status).toBe(502); expect(remote).toHaveBeenCalledTimes(1)
  })
  it('runs preview then textures and remembers the new task before downloading', async () => {
    const remote = vi.fn().mockResolvedValueOnce(Response.json({ id: 'preview-1234', status: 'SUCCEEDED', progress: 100, hasModel: true })).mockResolvedValueOnce(Response.json({ id: 'refine-5678' })).mockResolvedValueOnce(Response.json({ id: 'refine-5678', status: 'SUCCEEDED', progress: 100, hasModel: true }))
    vi.stubGlobal('fetch', remote); const saved: Job[] = []
    const result = await followJob({ id: 'preview-1234', prompt: 'dąb', stage: 'preview', textured: true }, 'key', new AbortController().signal, () => {}, job => saved.push(job))
    expect(result).toMatchObject({ id: 'refine-5678', previewId: 'preview-1234', stage: 'refine' })
    expect(saved.at(-1)).toEqual(result)
    expect(JSON.parse(remote.mock.calls[1][1].body)).toEqual({ action: 'refine', id: 'preview-1234', prompt: 'dąb' })
  })
  it('never retries a texture POST with uncertain outcome', async () => {
    const remote = vi.fn().mockResolvedValue(Response.json({ status: 'SUCCEEDED', progress: 100, hasModel: true })); vi.stubGlobal('fetch', remote)
    await expect(followJob({ id: 'preview-1234', prompt: 'dąb', stage: 'preview', textured: true, textureRequestUncertain: true }, 'key', new AbortController().signal, () => {}, () => {})).rejects.toThrow('Brak potwierdzenia')
    expect(remote).toHaveBeenCalledTimes(1)
  })
})
describe('optional dimensions and actual export', () => {
  it('preserves proportions by default and exports the adjusted geometry in millimetres', async () => {
    const source = new Group(); source.add(new Mesh(new BoxGeometry(2,4,2), new MeshBasicMaterial()))
    expect(modelSize(transformModel(source, EMPTY_ADJUSTMENTS))).toEqual([5,10,5])
    const adjusted = transformModel(source, { dimensions: ['', '5', ''], angles: ['', '', ''] })
    expect(modelSize(adjusted)).toEqual([2.5,5,2.5])
    const blob = await exportModel(adjusted, 'stl')
    const bytes = await new Promise<ArrayBuffer>((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result as ArrayBuffer); reader.onerror = reject; reader.readAsArrayBuffer(blob) })
    const view = new DataView(bytes), y: number[] = []
    for (let i = 0; i < view.getUint32(80,true); i++) for (let vertex = 0; vertex < 3; vertex++) y.push(view.getFloat32(84 + 50 * i + 12 + vertex * 12 + 4, true))
    expect(Math.max(...y) - Math.min(...y)).toBeCloseTo(50)
    expect(() => transformModel(source, { ...EMPTY_ADJUSTMENTS, dimensions: ['', '-2', ''] })).toThrow()
  })
  it('opens on freeform input with optional controls collapsed and clear connection setup', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({ configured: false })))
    render(<MemoryRouter><ModelStudio /></MemoryRouter>)
    const summary = screen.getByText('Wymiary i kąty · opcjonalnie')
    expect(summary.closest('details')?.open).toBe(false)
    expect(screen.queryByRole('heading', { name: 'Rakieta kosmiczna' })).toBeNull()
    fireEvent.change(screen.getByLabelText('Co mam stworzyć?'), { target: { value: 'A teraz zrób drzewo dąb' } })
    fireEvent.click(screen.getByRole('button', { name: /Generuj model 3D/ }))
    await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('podłącz konto Meshy'))
    expect(screen.getByText(/Połączenie AI ·/).closest('details')?.open).toBe(true)
  })
})
