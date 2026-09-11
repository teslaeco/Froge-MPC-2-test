import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Image3DSettings } from '../blender/Image3DSettings'
import { GenerationExports } from '../blender/GenerationExports'
import { supportsPhotoGeneration } from '../blender/compatibility'

afterEach(() => { cleanup(); vi.unstubAllGlobals() })
it('requires an image engine even when Astra is ready', () => {
  expect(supportsPhotoGeneration({ connectorVersion:20, photoInput:true, provider:'openai' })).toBe(false)
  expect(supportsPhotoGeneration({ connectorVersion:21, image3dRevision:1, image3dReady:false })).toBe(false)
  expect(supportsPhotoGeneration({ connectorVersion:21, image3dRevision:1, image3dReady:true, provider:'ollama' })).toBe(true)
})
it('sends the Meshy key only on explicit save and clears its field', async () => {
  const upstream = vi.fn(async () => Response.json({ saved:true }))
  vi.stubGlobal('fetch',upstream)
  const onSaved=vi.fn(async()=>{})
  render(<Image3DSettings connection={{ connected:true, ready:true, detail:'', connectorVersion:21 }} busy={false} onSaved={onSaved}/>)
  const input=screen.getByLabelText('Klucz API Meshy')
  fireEvent.change(input,{target:{value:'offline-fixture-meshy-key-123456789'}})
  expect(upstream).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button',{name:'Podłącz Meshy'}))
  await waitFor(()=>expect(onSaved).toHaveBeenCalledOnce())
  expect(input).toHaveValue('')
  const [url,init]=upstream.mock.calls[0] as unknown as [string,RequestInit]
  expect(url).toBe('/api/blender/image3d')
  expect(JSON.parse(String(init.body))).toMatchObject({provider:'meshy',textureResolution:'8k'})
})
it('offers the original and FBX files and labels a smaller preview', async () => {
  vi.stubGlobal('fetch',vi.fn(async()=>Response.json({formats:[{format:'master',bytes:60000000},{format:'fbx',bytes:45000000}],quality:{texturesReduced:true,masterTextures:[{name:'base color',size:[8192,8192]}]}})))
  render(<GenerationExports jobId="fixture-job"/>)
  expect(await screen.findByRole('link',{name:/Pełny GLB/})).toHaveAttribute('href','/api/blender/jobs/fixture-job/exports/master')
  expect(screen.getByRole('link',{name:/FBX/})).toHaveAttribute('href','/api/blender/jobs/fixture-job/exports/fbx')
  expect(screen.getByText(/Podgląd ma mniejsze tekstury/)).toBeInTheDocument()
  expect(screen.getByText('base color: 8192 × 8192 px')).toBeInTheDocument()
})
