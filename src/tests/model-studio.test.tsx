/// <reference types="node" />
import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { inflateSync } from 'node:zlib'
import App from '../App'
import { buildMesh, createModel, exportStl, INITIAL_PROMPT, INITIAL_SPEC, parseCommand, specSchema } from '../studio/model'
import { getStudio, updateStudio, undoStudio } from '../studio/store'
import { studioTools } from '../studio/tools'

afterEach(cleanup)
describe('parametric model and exports', () => {
  it('parses the Polish 1 × 1 × 5 cm rocket with unit conversion', () => {
    const result = parseCommand(INITIAL_PROMPT, INITIAL_SPEC)
    expect(result.errors).toEqual([])
    expect(result.spec.diameter).toBe(10); expect(result.spec.height).toBe(50)
    expect(parseCommand('wysokość pięć centymetrów', INITIAL_SPEC).spec.height).toBe(50)
    expect(parseCommand('średnica 1,2 cm', INITIAL_SPEC).spec.diameter).toBe(12)
  })
  it('rejects conflicting diameters, unitless values, invalid angles and unsupported shapes', () => {
    for (const text of ['szerokość 1 cm długość 2 cm', 'wysokość 0 cm', 'wysokość 50', 'wysokość 4 cm wysokość 5 cm', 'kąt nosa 5 stopni', 'zrób model smoka']) {
      const result = parseCommand(text, INITIAL_SPEC)
      expect(result.errors.length, text).toBeGreaterThan(0)
      expect(result.spec, text).toEqual(INITIAL_SPEC)
    }
    expect(specSchema.safeParse({ ...INITIAL_SPEC, diameter: Infinity }).success).toBe(false)
    expect(specSchema.safeParse({ ...INITIAL_SPEC, segments: 10000 }).success).toBe(false)
  })
  it('exports the exact preview positions in metres and an outward closed rocket shell', () => {
    const model = createModel(INITIAL_SPEC)
    expect(model.qa.sizeMm[0]).toBeCloseTo(10, 8); expect(model.qa.sizeMm[1]).toBeCloseTo(50, 8); expect(model.qa.sizeMm[2]).toBeCloseTo(10, 8)
    const bytes = Buffer.from(model.gltf.buffers[0].uri.split(',')[1], 'base64')
    for (let i = 0; i < model.mesh.positions.length; i++) expect(bytes.readFloatLE(i * 4)).toBeCloseTo(model.mesh.positions[i], 8)
    const edges = new Map<string, number>(); let volume = 0
    const p = (i: number) => model.mesh.positions.slice(i * 3, i * 3 + 3)
    const key = (a: number[]) => a.map(v => (Math.abs(v) < 1e-10 ? 0 : v).toFixed(10)).join(',')
    for (let i = 0; i < model.mesh.indices.length; i += 3) {
      const [a,b,c] = model.mesh.indices.slice(i,i+3).map(p)
      volume += (a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
      for (const [x,y] of [[a,b],[b,c],[c,a]]) { const e = [key(x),key(y)].sort().join('|'); edges.set(e, (edges.get(e)??0)+1) }
    }
    expect([...edges.values()].every(n => n === 2)).toBe(true)
    expect(volume).toBeGreaterThan(0)
    const stl = exportStl(model.mesh)
    const vertices = [...stl.matchAll(/vertex (-?[\d.e+-]+) (-?[\d.e+-]+) (-?[\d.e+-]+)/g)]
    expect(vertices.length).toBe(model.mesh.indices.length)
    expect(Math.max(...vertices.map(v => Number(v[2])))).toBeCloseTo(50)
  })
  it('writes a real decodable PNG matching the embedded texture and material changes', () => {
    const model = createModel(INITIAL_SPEC), b = Buffer.from(model.texture)
    expect(b.subarray(0,8)).toEqual(Buffer.from([137,80,78,71,13,10,26,10]))
    let i = 8, raw: Buffer | undefined
    while (i < b.length) { const len = b.readUInt32BE(i); if (b.toString('ascii',i+4,i+8)==='IDAT') raw=inflateSync(b.subarray(i+8,i+8+len)); i+=12+len }
    expect(raw?.length).toBe(128*(128*3+1))
    expect(Buffer.from(model.gltf.images[0].uri.split(',')[1],'base64')).toEqual(b)
    const blue = createModel({ ...INITIAL_SPEC, color: '#3691ed', material: 'carbon' })
    expect(blue.texture).not.toEqual(model.texture)
    expect(blue.mesh).toEqual(model.mesh)
    expect(createModel({...INITIAL_SPEC,fins:true}).qa.sizeMm[0]).toBeCloseTo(16)
    expect(createModel({...INITIAL_SPEC,fins:true}).qa.intersectingFinShells).toBe(true)
    expect(createModel({...INITIAL_SPEC,segments:256}).qa.circularChordErrorMm).toBeLessThan(model.qa.circularChordErrorMm)
  })
  it('creates each supported primitive without invalid coordinates or normals', () => {
    for (const shape of ['rocket','cylinder','cone','sphere'] as const) {
      const mesh = buildMesh({...INITIAL_SPEC,shape,height:shape==='sphere'?10:50})
      expect(mesh.positions.every(Number.isFinite)).toBe(true); expect(mesh.normals.every(Number.isFinite)).toBe(true)
      expect(mesh.texcoords.length).toBe(mesh.positions.length/3*2)
      expect(mesh.indices.every(i=>i>=0 && i<mesh.positions.length/3)).toBe(true)
    }
  })
})
describe('home studio and agent integration', () => {
  it('places the editor on home and changes geometry through controls and text', () => {
    updateStudio({...INITIAL_SPEC})
    render(<MemoryRouter><App /></MemoryRouter>)
    expect(screen.getByRole('heading',{name:'Powiedz, co tworzymy.'})).toBeTruthy()
    expect(screen.queryByTitle('Terra Observatory live application')).toBeNull()
    fireEvent.click(screen.getByRole('button',{name:'Bryły parametryczne'}))
    fireEvent.change(screen.getByLabelText('Wysokość'),{target:{value:'6'}})
    expect(getStudio().spec.height).toBe(60)
    fireEvent.change(screen.getByLabelText('Co mam stworzyć lub zmienić?'),{target:{value:'Kolor niebieski'}})
    fireEvent.click(screen.getByRole('button',{name:/Zastosuj polecenie/}))
    expect(getStudio().spec.color).toBe('#3691ed')
    fireEvent.change(screen.getByLabelText('Co mam stworzyć lub zmienić?'),{target:{value:'średnica 0 cm'}})
    fireEvent.click(screen.getByRole('button',{name:/Zastosuj polecenie/}))
    expect(screen.getByRole('alert')).toBeTruthy(); expect(getStudio().spec.diameter).toBe(10)
  })
  it('updates the same live store via WebMCP, rejects stale writes and can undo', async () => {
    updateStudio({...INITIAL_SPEC}); const before = getStudio()
    const edit = studioTools.find(t=>t.name==='update_live_3d_studio')!
    expect(await edit.execute({spec:{...before.spec,height:65},expectedRevision:before.revision})).toMatchObject({state:'PASS'})
    expect(getStudio().spec.height).toBe(65)
    expect(await edit.execute({spec:{...before.spec,height:70},expectedRevision:before.revision})).toMatchObject({state:'CONFLICT'})
    undoStudio(); expect(getStudio().spec).toEqual(before.spec)
    expect(await edit.execute({spec:{...before.spec,height:-1},expectedRevision:getStudio().revision})).toMatchObject({state:'FAIL'})
  })
})
