// Reproducible local browser assets. No photo is sent to the asset provider.
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const target = path.join(root, 'public/face-fit')
const hashes = {
  'face_landmarker.task': '64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff',
  'vision_wasm_internal.js': '4a97e2520ba506c680ecd6ba6acfb146888afa0e2746d57f205352bc6ebb82eb',
  'vision_wasm_internal.wasm': 'f00ec4731faa23b3e714d00e88d4d10e2df5c0a427d3a2b4ae6e3526fdd14ef7',
  'vision_wasm_nosimd_internal.js': '927def7b465c51b86e4b3060f93646aca4e27121f4b8fc0483786e407ea9cf1f',
  'vision_wasm_nosimd_internal.wasm': '3821ea9b1f7fb8c549ef2a064ef5c85750bf375c545a49fd6eea0df44a95f1f4',
}
const digest = data => createHash('sha256').update(data).digest('hex')
await mkdir(target, { recursive: true })
for (const [name, sha] of Object.entries(hashes)) {
  const destination = path.join(target, name)
  try { if (digest(await readFile(destination)) === sha) continue } catch (e) { if (e.code !== 'ENOENT') throw e }
  let data
  if (name.endsWith('.task')) {
    const response = await fetch('https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task', { signal: AbortSignal.timeout(60000) })
    if (!response.ok) throw new Error('Cannot fetch pinned face measurement model: ' + response.status)
    data = Buffer.from(await response.arrayBuffer())
  } else data = await readFile(path.join(root, 'node_modules/@mediapipe/tasks-vision/wasm', name))
  if (digest(data) !== sha) throw new Error('Face measurement asset checksum mismatch: ' + name)
  await writeFile(destination, data)
}
console.log('Verified pinned face measurement assets')
