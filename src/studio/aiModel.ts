import { Box3, Group, LoadingManager, Mesh, Vector3, type Texture, type Material } from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js'
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js'
import { STLExporter } from 'three/addons/exporters/STLExporter.js'

export type Adjustments = { dimensions: [string, string, string]; angles: [string, string, string] }
export const EMPTY_ADJUSTMENTS: Adjustments = { dimensions: ['', '', ''], angles: ['', '', ''] }
export function transformModel(source: Group, options: Adjustments): Group {
  const box = new Box3().setFromObject(source), size = box.getSize(new Vector3()), center = box.getCenter(new Vector3())
  if (size.toArray().some(v => !Number.isFinite(v) || v <= 0)) throw new Error('Model ma nieprawidłowe gabaryty.')
  const dimensions = options.dimensions.map(v => v.trim() === '' ? null : Number(v.replace(',', '.')))
  const angles = options.angles.map(v => v.trim() === '' ? 0 : Number(v.replace(',', '.')))
  if (dimensions.some(v => v !== null && (!Number.isFinite(v) || v < 0.1 || v > 1000))) throw new Error('Opcjonalny wymiar powinien wynosić od 0,1 do 1000 cm.')
  if (angles.some(v => !Number.isFinite(v) || Math.abs(v) > 360)) throw new Error('Kąt obrotu powinien wynosić od −360° do 360°.')
  const first = dimensions.findIndex(v => v !== null)
  const factor = first < 0 ? 0.1 / Math.max(size.x, size.y, size.z) : dimensions[first]! / 100 / size.toArray()[first]
  const centered = new Group(); centered.add(source.clone(true)); centered.position.copy(center).multiplyScalar(-1)
  const scaled = new Group(); scaled.add(centered)
  scaled.scale.set(...dimensions.map((v, i) => v === null ? factor : v / 100 / size.toArray()[i]) as [number, number, number])
  const result = new Group(); result.add(scaled); result.rotation.set(...angles.map(v => v * Math.PI / 180) as [number,number,number]); result.updateMatrixWorld(true)
  return result
}
export async function loadModel(bytes: ArrayBuffer): Promise<Group> {
  const manager = new LoadingManager()
  // GLB must be self-contained. Never fetch arbitrary URLs embedded in a model.
  manager.setURLModifier(url => {
    if (url.startsWith('blob:') || url.startsWith('data:') || url.startsWith('/draco/')) return url
    throw new Error('Model zawiera zewnętrzny zasób. Pobierz samodzielny plik GLB.')
  })
  const draco = new DRACOLoader(manager).setDecoderPath('/draco/')
  try {
    const model = await new GLTFLoader(manager).setDRACOLoader(draco).parseAsync(bytes, '')
    let triangles = 0
    model.scene.traverse(object => { if (object instanceof Mesh) triangles += (object.geometry.index?.count ?? object.geometry.getAttribute('position')?.count ?? 0) / 3 })
    if (!triangles || triangles > 1000000) { disposeModel(model.scene); throw new Error('Siatka jest pusta lub zbyt duża dla podglądu.') }
    return model.scene
  } finally { draco.dispose() }
}
export function disposeModel(root: Group) {
  const materials = new Set<Material>(), textures = new Set<Texture>()
  root.traverse(object => { if (object instanceof Mesh) { object.geometry.dispose(); for (const mat of Array.isArray(object.material) ? object.material : [object.material]) materials.add(mat) } })
  for (const material of materials) { for (const value of Object.values(material)) if (value?.isTexture) textures.add(value); material.dispose() }
  for (const texture of textures) { texture.dispose(); const data = texture.source?.data as { close?: () => void } | undefined; if (typeof data?.close === 'function') data.close() }
}
export function modelSize(root: Group) { return new Box3().setFromObject(root).getSize(new Vector3()).toArray().map(v => v * 100) }
export async function exportModel(root: Group, format: 'glb' | 'stl') {
  if (format === 'glb') return new Blob([await new GLTFExporter().parseAsync(root, { binary: true }) as ArrayBuffer], { type: 'model/gltf-binary' })
  const mm = new Group(); mm.add(root.clone(true)); mm.scale.setScalar(1000); mm.updateMatrixWorld(true)
  const data = new STLExporter().parse(mm, { binary: true })
  return new Blob([new Uint8Array(data.buffer as ArrayBuffer)], { type: 'model/stl' })
}
