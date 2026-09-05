import { z } from 'zod'

export const specSchema = z.object({
  shape: z.enum(['rocket', 'cylinder', 'cone', 'sphere']),
  diameter: z.number().min(1).max(500), height: z.number().min(2).max(1000),
  noseAngle: z.number().min(20).max(120), segments: z.number().int().min(32).max(256).refine(n => n % 4 === 0),
  color: z.string().regex(/^#[0-9a-f]{6}$/i), accent: z.string().regex(/^#[0-9a-f]{6}$/i),
  material: z.enum(['metal', 'ceramic', 'carbon']), windows: z.boolean(), fins: z.boolean(),
}).strict().superRefine((s, ctx) => {
  if (s.shape === 'rocket' && (s.diameter / 2) / Math.tan(s.noseAngle * Math.PI / 360) > s.height * .7)
    ctx.addIssue({ code: 'custom', message: 'Stożek jest za długi: zwiększ kąt nosa lub wysokość, albo zmniejsz średnicę.' })
  if (s.shape === 'sphere' && s.height !== s.diameter)
    ctx.addIssue({ code: 'custom', message: 'Kula wymaga jednakowej wysokości i średnicy.' })
})
export type ModelSpec = z.infer<typeof specSchema>
export const INITIAL_SPEC: ModelSpec = { shape: 'rocket', diameter: 10, height: 50, noseAngle: 40, segments: 128, color: '#e2e8ed', accent: '#f07845', material: 'metal', windows: true, fins: false }
export const SHAPE_NAMES = { rocket: 'Rakieta kosmiczna', cylinder: 'Walec', cone: 'Stożek', sphere: 'Kula' }
export const INITIAL_PROMPT = 'Zrób rakietę kosmiczną, szerokość 1 cm, długość 1 cm, wysokość 5 cm, okrągły przekrój, metal z teksturą i oknem.'
export function normalizeText(text: string) {
  return text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/ł/g, 'l')
    .replace(/(\d),(\d)/g, '$1.$2')
    .replace(/\b(jeden|jedna|dwa|dwie|trzy|cztery|piec|szesc|siedem|osiem|dziewiec|dziesiec)\b/g, x => String(({ jeden: 1, jedna: 1, dwa: 2, dwie: 2, trzy: 3, cztery: 4, piec: 5, szesc: 6, siedem: 7, osiem: 8, dziewiec: 9, dziesiec: 10 } as Record<string, number>)[x]))
}
export function parseCommand(command: string, previous: ModelSpec) {
  const t = normalizeText(command), next = { ...previous }, applied: string[] = [], errors: string[] = []
  const shapes: [RegExp, ModelSpec['shape']][] = [[/rakiet|rocket/, 'rocket'], [/walec|walca|cylinder/, 'cylinder'], [/stozek|stozka|cone/, 'cone'], [/\bkula\b|\bkule\b|sphere/, 'sphere']]
  for (const [pattern, shape] of shapes) if (pattern.test(t)) { next.shape = shape; applied.push(SHAPE_NAMES[shape]); break }
  if (/\b(slon|konia|kon|smok|smoka|dom|samochod|pies|kota|kot|dragon|car|dog)\b/.test(t)) errors.push('Ten kształt wymaga generatora AI. Obecnie dostępne: rakieta, walec, stożek i kula.')
  const values: Record<string, number[]> = {}
  const rx = /\b(wysokosc(?:i)?|wysokoscia|height|srednic[aeay]?|diameter|szerokosc(?:i)?|width|dlugosc(?:i)?|depth)\s*(?:[:=]|na|do|o|to)?\s*(-?\d+(?:\.\d+)?)\s*(milimetr\w*|centymetr\w*|metr\w*|mm|cm|m)?\b/g
  for (const m of t.matchAll(rx)) {
    if (!m[3]) { errors.push(`Podaj jednostkę mm lub cm przy „${m[1]}”.`); continue }
    const unit = m[3], v = Number(m[2]) * (/^(cm|centymetr)/.test(unit) ? 10 : /^(m$|metr)/.test(unit) ? 1000 : 1)
    const key = /wysok|height/.test(m[1]) ? 'height' : /szerok|width/.test(m[1]) ? 'width' : /dlug|depth/.test(m[1]) ? 'depth' : 'diameter'
    ;(values[key] ??= []).push(v)
  }
  const diameters = ['diameter', 'width', 'depth'].filter(k => values[k]).map(k => values[k].at(-1)!)
  if (diameters.length && diameters.some(v => v !== diameters[0])) errors.push('Okrągły przekrój wymaga szerokości równej głębokości. Podaj jedną średnicę.')
  if (diameters.length) { next.diameter = diameters[0]; applied.push(`średnica ${next.diameter} mm`) }
  if (values.height) { next.height = values.height.at(-1)!; applied.push(`wysokość ${next.height} mm`) }
  if (Object.values(values).some(list => new Set(list).size > 1)) errors.push('W poleceniu są sprzeczne wymiary tej samej osi. Podaj jeden końcowy wymiar.')
  const angle = t.match(/(?:kat(?:em)?(?: nosa| stozka)?|angle)\s*(?:[:=]|na|do)?\s*(-?\d+(?:\.\d+)?)\s*(?:°|stopni|degrees)/)
  if (angle) { next.noseAngle = Number(angle[1]); applied.push(`kąt nosa ${next.noseAngle}°`) }
  if (/bez ok(?:na|ien)|usun ok/.test(t)) { next.windows = false; applied.push('bez okna') }
  else if (/okno|oknem|okna|window/.test(t)) { next.windows = true; applied.push('okno na teksturze') }
  if (/bez lotek|usun lotki/.test(t)) { next.fins = false; applied.push('bez lotek') }
  else if (/lotki|lotkami|fins/.test(t)) { next.fins = true; applied.push('4 lotki') }
  const colors: [RegExp, string][] = [[/czerwon/, '#e24b4b'], [/niebiesk/, '#3691ed'], [/zielon/, '#51bd90'], [/zol[ty]/, '#efc64a'], [/czarn/, '#343945'], [/bial/, '#edf0f2'], [/srebrn/, '#c2cbd5'], [/pomarancz/, '#f07845']]
  for (const [pattern, hex] of colors) if (pattern.test(t)) { next.color = hex; applied.push(`kolor ${hex}`); break }
  const hex = t.match(/#[0-9a-f]{6}\b/)
  if (hex) { next.color = hex[0]; applied.push(`kolor ${hex[0]}`) }
  for (const [pattern, material] of [[/metal/, 'metal'], [/ceramik/, 'ceramic'], [/karbon|carbon|weglow/, 'carbon']] as const)
    if (pattern.test(t)) { next.material = material; applied.push(`materiał ${material}`) }
  if (next.shape === 'sphere') {
    if (values.height && diameters.length && next.height !== next.diameter) errors.push('Kula ma tę samą średnicę we wszystkich osiach.')
    else next.height = next.diameter = values.height ? next.height : next.diameter
  }
  const validated = specSchema.safeParse(next)
  if (!validated.success) errors.push(...validated.error.issues.map(e => e.message))
  if (!applied.length) errors.push('Nie rozpoznano zmiany. Spróbuj: „wysokość 6 cm”, „średnica 12 mm”, „kąt nosa 50 stopni” lub „kolor niebieski”.')
  return { spec: errors.length ? previous : next, applied, errors }
}

export type Mesh = { positions: number[]; normals: number[]; texcoords: number[]; indices: number[] }
type V = [number, number, number]
function triangle(m: Mesh, a: V, b: V, c: V, uvs: number[] = [0, 0, 1, 0, 0, 1]) {
  const ab = b.map((v, i) => v - a[i]), ac = c.map((v, i) => v - a[i])
  const n = [ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0]]
  const l = Math.hypot(...n)
  if (l < 1e-20) return
  const start = m.positions.length / 3
  m.positions.push(...a, ...b, ...c); m.normals.push(...n.map(v => v / l), ...n.map(v => v / l), ...n.map(v => v / l)); m.texcoords.push(...uvs); m.indices.push(start, start + 1, start + 2)
}
export function buildMesh(input: ModelSpec): Mesh {
  const s = specSchema.parse(input), r = s.diameter / 2000, h = s.height / 1000, n = s.segments
  const nose = r / Math.tan(s.noseAngle * Math.PI / 360)
  const profile: [number, number][] = s.shape === 'sphere'
    ? Array.from({ length: 49 }, (_, i) => [h * (1 - Math.cos(Math.PI * i / 48)) / 2, r * Math.sin(Math.PI * i / 48)])
    : s.shape === 'cone' ? [[0, 0], [0, r], [h, 0]]
    : s.shape === 'cylinder' ? [[0, 0], [0, r], [h, r], [h, 0]]
    : [[0, 0], [0, r * .55], [h * .055, r * .4], [h * .10, r], [h - nose, r], [h, 0]]
  const m: Mesh = { positions: [], normals: [], texcoords: [], indices: [] }
  for (let ring = 0; ring < profile.length - 1; ring++) {
    const [y0, r0] = profile[ring], [y1, r1] = profile[ring + 1]
    const normal = (a: number): V => { const l = Math.hypot(y1 - y0, r0 - r1); return [(y1 - y0) * Math.cos(a) / l, (r0 - r1) / l, (y1 - y0) * Math.sin(a) / l] }
    for (let j = 0; j < n; j++) {
      const a = j * 2 * Math.PI / n, b = (j + 1) * 2 * Math.PI / n
      const p: V = [r0 * Math.cos(a), y0, r0 * Math.sin(a)], q: V = [r0 * Math.cos(b), y0, r0 * Math.sin(b)]
      const t: V = [r1 * Math.cos(a), y1, r1 * Math.sin(a)], u: V = [r1 * Math.cos(b), y1, r1 * Math.sin(b)]
      const add = (v1: V, v2: V, v3: V, angles: number[], uv: number[]) => {
        const start = m.normals.length; triangle(m, v1, v2, v3, uv)
        if (m.normals.length > start) m.normals.splice(start, 9, ...angles.flatMap(normal))
      }
      add(p, t, q, [a, a, b], [j / n, 1 - y0 / h, j / n, 1 - y1 / h, (j + 1) / n, 1 - y0 / h])
      add(q, t, u, [b, a, b], [(j + 1) / n, 1 - y0 / h, j / n, 1 - y1 / h, (j + 1) / n, 1 - y1 / h])
    }
  }
  // Four closed fin shells. Intersections with the body still need a manufacturing union.
  if (s.shape === 'rocket' && s.fins) for (let k = 0; k < 4; k++) {
    const angle = k * Math.PI / 2
    const v = (x: number, y: number, z: number): V => [x * Math.cos(angle) - z * Math.sin(angle), y, x * Math.sin(angle) + z * Math.cos(angle)]
    const a = v(r * .85, h * .12, -r * .07), b = v(r * 1.6, h * .08, -r * .07), c = v(r * .85, h * .38, -r * .07)
    const d = v(r * .85, h * .12, r * .07), e = v(r * 1.6, h * .08, r * .07), f = v(r * .85, h * .38, r * .07)
    for (const face of [[a,c,b],[d,e,f],[a,b,e],[a,e,d],[b,c,f],[b,f,e],[c,a,d],[c,d,f]]) triangle(m, face[0], face[1], face[2])
  }
  return m
}

function concat(parts: Uint8Array[]) { const b = new Uint8Array(parts.reduce((a, v) => a + v.length, 0)); let offset = 0; for (const p of parts) { b.set(p, offset); offset += p.length } return b }
function be(n: number) { return new Uint8Array([n >>> 24, n >>> 16, n >>> 8, n]) }
function crc(b: Uint8Array) { let c = 0xffffffff; for (const v of b) { c ^= v; for (let i = 0; i < 8; i++) c = (c >>> 1) ^ ((c & 1) ? 0xedb88320 : 0) } return (c ^ 0xffffffff) >>> 0 }
function chunk(type: string, b: Uint8Array) { const data = concat([new TextEncoder().encode(type), b]); return concat([be(b.length), data, be(crc(data))]) }
export function base64(bytes: Uint8Array) { let s = ''; for (const b of bytes) s += String.fromCharCode(b); return btoa(s) }
export function fingerprint(input: string) { let h = 2166136261; for (const c of input) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return (h >>> 0).toString(16).padStart(8, '0') }
export function texturePng(s: ModelSpec) {
  const size = 128, raw = new Uint8Array((size * 3 + 1) * size)
  const rgb = (hex: string) => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16))
  const main = rgb(s.color), accent = rgb(s.accent)
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const u = x / size, v = y / size
    const stripe = v > .79 && v < .84 || v < .12
    const panel = s.material === 'metal' && (x % 32 === 0 || y % 24 === 0)
    const weave = s.material === 'carbon' ? ((Math.floor(x / 4) + Math.floor(y / 4)) % 2 ? .55 : .78) : .96 + .04 * Math.sin(x * 3 + y)
    const windowRadius = Math.hypot((u - .25) * Math.PI * s.diameter, (v - .47) * s.height)
    const window = s.shape === 'rocket' && s.windows && windowRadius < s.diameter * .23
    const c = window ? windowRadius > s.diameter * .18 ? accent : [28 + y / 3, 112 + y / 2, 175 + x / 2] : stripe ? accent : panel ? main.map(v => v * .6) : main.map(v => v * weave)
    raw.set(c.map(v => Math.round(Math.min(255, v))), y * (size * 3 + 1) + 1 + x * 3)
  }
  let a = 1, b = 0; for (const v of raw) { a = (a + v) % 65521; b = (b + a) % 65521 }
  const len = raw.length
  const compressed = concat([new Uint8Array([120, 1, 1, len & 255, len >> 8, ~len & 255, ~len >> 8 & 255]), raw, be((b << 16) | a)])
  return concat([new Uint8Array([137,80,78,71,13,10,26,10]), chunk('IHDR', concat([be(size), be(size), new Uint8Array([8,2,0,0,0])])), chunk('IDAT', compressed), chunk('IEND', new Uint8Array())])
}
export function bounds(mesh: Mesh) {
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity]
  mesh.positions.forEach((v, i) => { min[i % 3] = Math.min(min[i % 3], v); max[i % 3] = Math.max(max[i % 3], v) })
  return { min, max, sizeMm: max.map((v, i) => (v - min[i]) * 1000) }
}
export function createModel(s: ModelSpec) {
  const mesh = buildMesh(s), texture = texturePng(s), box = bounds(mesh), id = fingerprint(JSON.stringify(s))
  const views = [new Float32Array(mesh.positions), new Float32Array(mesh.normals), new Float32Array(mesh.texcoords), new Uint32Array(mesh.indices)].map(a => new Uint8Array(a.buffer))
  let offset = 0
  const bufferViews = views.map((v, i) => { const result = { buffer: 0, byteOffset: offset, byteLength: v.length, target: i === 3 ? 34963 : 34962 }; offset += v.length; return result })
  const data = concat(views)
  const qa = { finite: mesh.positions.every(Number.isFinite), indexRange: mesh.indices.every(i => i >= 0 && i < mesh.positions.length / 3), sizeMm: box.sizeMm, manufacturingReady: false, intersectingFinShells: s.shape === 'rocket' && s.fins, circularChordErrorMm: (s.diameter / 2) * (1 - Math.cos(Math.PI / s.segments)) }
  const gltf = {
    asset: { version: '2.0', generator: 'Froge parametric studio 2' }, scene: 0, scenes: [{ nodes: [0] }], nodes: [{ mesh: 0, name: SHAPE_NAMES[s.shape] }],
    meshes: [{ primitives: [{ attributes: { POSITION: 0, NORMAL: 1, TEXCOORD_0: 2 }, indices: 3, material: 0 }] }],
    buffers: [{ byteLength: data.length, uri: `data:application/octet-stream;base64,${base64(data)}` }], bufferViews,
    accessors: [
      { bufferView: 0, componentType: 5126, count: mesh.positions.length / 3, type: 'VEC3', min: box.min, max: box.max },
      { bufferView: 1, componentType: 5126, count: mesh.normals.length / 3, type: 'VEC3' },
      { bufferView: 2, componentType: 5126, count: mesh.texcoords.length / 2, type: 'VEC2' },
      { bufferView: 3, componentType: 5125, count: mesh.indices.length, type: 'SCALAR' },
    ],
    materials: [{ pbrMetallicRoughness: { baseColorTexture: { index: 0 }, metallicFactor: s.material === 'metal' ? .7 : .05, roughnessFactor: s.material === 'ceramic' ? .3 : .5 } }],
    images: [{ uri: `data:image/png;base64,${base64(texture)}` }], textures: [{ source: 0, sampler: 0 }], samplers: [{ magFilter: 9729, minFilter: 9729, wrapS: 10497, wrapT: 33071 }],
    extras: { spec: s, units: 'metres', sourceUnits: 'millimetres', qa, version: id, llmUsed: false },
  }
  return { mesh, texture, gltf, qa, id }
}
export function exportStl(mesh: Mesh) {
  const lines = ['solid Froge_model_mm']
  for (let i = 0; i < mesh.indices.length; i += 3) {
    const vertices = mesh.indices.slice(i, i + 3).map(k => mesh.positions.slice(k * 3, k * 3 + 3).map(v => v * 1000))
    const [a,b,c] = vertices, ab = b.map((v,k) => v-a[k]), ac = c.map((v,k) => v-a[k])
    const n = [ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]], l = Math.hypot(...n)
    lines.push(`facet normal ${n.map(v => v/l).join(' ')}`, 'outer loop', ...vertices.map(v => `vertex ${v.join(' ')}`), 'endloop', 'endfacet')
  }
  return [...lines, 'endsolid Froge_model_mm'].join('\n')
}
