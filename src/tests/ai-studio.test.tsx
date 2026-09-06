import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { BoxGeometry, Group, Mesh, MeshBasicMaterial } from 'three'
import { ModelStudio } from '../components/ModelStudio'
import worker from '../studio/server'
import { exportModel, modelSize, transformModel, EMPTY_ADJUSTMENTS } from '../studio/aiModel'
import { sceneSchema,sceneModel,type ModelScene } from '../studio/scene'
import { getAgentScene,requestAgentModel,applyAgentScene,invalidateAgentRequest } from '../studio/agentSceneStore'
import { agentSceneTools } from '../studio/agentSceneTools'
afterEach(()=>{cleanup();vi.unstubAllGlobals();invalidateAgentRequest()})
const example:ModelScene={version:1,name:'Custom tetrahedron',description:'Arbitrary mesh',parts:[{name:'Part',vertices:[0,0,0, 1,0,0, 0,1,0, 0,0,1],triangles:[0,2,1,0,1,3,0,3,2,1,2,3],uv:[0,0,1,0,0,1,1,1],color:'#218a56',roughness:.6,metalness:0,pattern:'scales'}]}
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
})

describe('Codex and Blender modeling',()=>{
 it('accepts arbitrary geometry and rejects bad indices, UV and executable fields',()=>{
  expect(sceneModel(example).children).toHaveLength(1)
  expect(sceneSchema.safeParse({...example,code:'do something'}).success).toBe(false)
  expect(sceneSchema.safeParse({...example,parts:[{...example.parts[0],triangles:[0,1,99]}]}).success).toBe(false)
  expect(sceneSchema.safeParse({...example,parts:[{...example.parts[0],uv:[]}]}).success).toBe(false)
 })
 it('applies an agent model and refuses stale requests or results after manual import',async()=>{
  requestAgentModel('Zrób drzewo dąb');const before=getAgentScene()
  expect(await agentSceneTools.find(t=>t.name==='apply_3d_model_scene')!.execute({scene:example,expectedRevision:before.revision,requestId:before.request!.id})).toMatchObject({state:'PASS'})
  expect(getAgentScene().scene?.name).toBe(example.name)
  requestAgentModel('Teraz zrób smoka')
  expect(applyAgentScene(example,before.revision,before.request!.id).state).toBe('CONFLICT')
  const pending=getAgentScene();invalidateAgentRequest()
  expect(applyAgentScene(example,pending.revision,pending.request!.id).state).toBe('CONFLICT')
 })
 it('does not call a paid provider and retires the former API',async()=>{
  const remote=vi.fn();vi.stubGlobal('fetch',remote)
  const result=await worker.fetch(new Request('https://studio.test/api/3d/tasks',{method:'POST'}),{ASSETS:{fetch:async()=>new Response('asset')}})
  expect(result.status).toBe(410);expect(remote).not.toHaveBeenCalled()
 })
 it('keeps dimensions optional and queues a manual agent request without submitting a generation job',()=>{
  const remote=vi.fn(async(url)=>Response.json(String(url).endsWith('/connection')?{connected:false,ready:false}:{jobs:[]}));vi.stubGlobal('fetch',remote)
  render(<MemoryRouter><ModelStudio/></MemoryRouter>)
  expect(screen.getByText('Wymiary i kąty · opcjonalnie').closest('details')?.open).toBe(false)
  expect(screen.queryByLabelText('Klucz API Meshy')).toBeNull()
  expect(screen.getByRole('link',{name:/Pobierz dodatek do Blendera/}).getAttribute('href')).toBe('/downloads/froge-blender-addon.zip')
  fireEvent.change(screen.getByLabelText('Co mam stworzyć?'),{target:{value:'Zrób smoka'}})
  fireEvent.click(screen.getByText('Praca z Codexem przez WebMCP'))
  fireEvent.click(screen.getByRole('button',{name:/Przygotuj polecenie dla agenta/}))
  expect(getAgentScene().status).toBe('waiting');expect(getAgentScene().scene).toBeNull();expect(remote.mock.calls.every(([url])=>String(url).startsWith('/api/blender/'))).toBe(true)
 })
})
