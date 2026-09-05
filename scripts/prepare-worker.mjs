import { mkdir, copyFile, cp, readdir, rm } from 'node:fs/promises'
// Keep only the Worker and its public assets, removing obsolete static build files.
for (const name of await readdir('dist')) if (!['client', 'server', '.openai'].includes(name)) await rm('dist/' + name, { recursive: true, force: true })
await mkdir('dist/.openai', { recursive: true })
await copyFile('.openai/hosting.json', 'dist/.openai/hosting.json')
await cp('drizzle', 'dist/.openai/drizzle', { recursive: true })
await cp('node_modules/three/examples/jsm/libs/draco/gltf', 'dist/client/draco', { recursive: true })
