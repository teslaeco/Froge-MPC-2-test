import { useEffect, useRef, useState } from 'react'
import { ACESFilmicToneMapping, Box3, Color, DirectionalLight, PerspectiveCamera, PMREMGenerator, Scene, Vector3, WebGLRenderer, type Group } from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js'

type View = 'all' | 'face' | 'clothes' | 'shoes' | 'back'

export default function AiModelViewer({ model }: { model: Group }) {
  const host = useRef<HTMLDivElement>(null), fitView = useRef<((view?: View) => void) | null>(null)
  const [error, setError] = useState('')
  const [person, setPerson] = useState(false)
  useEffect(() => {
    const element = host.current; if (!element) return
    let renderer: WebGLRenderer
    try { renderer = new WebGLRenderer({ antialias: true, alpha: false }) } catch { setError('Podgląd 3D wymaga WebGL. Nadal możesz pobrać plik modelu.'); return }
    setError('')
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); renderer.setClearColor(new Color('#070e18'))
    renderer.toneMapping = ACESFilmicToneMapping; renderer.toneMappingExposure = 1
    element.appendChild(renderer.domElement)
    renderer.domElement.setAttribute('aria-label', 'Wygenerowany model 3D — przeciągnij, aby obrócić, uszczypnij, aby przybliżyć')
    const scene = new Scene(); scene.add(model)
    let isPerson = false; model.traverse(object => { if (object.userData.froge_kind === 'person') isPerson = true }); setPerson(isPerson)
    const pmrem = new PMREMGenerator(renderer), room = new RoomEnvironment()
    const environment = pmrem.fromScene(room, .04)
    scene.environment = environment.texture; scene.environmentIntensity = .6
    room.dispose(); pmrem.dispose()
    const light = new DirectionalLight(0xfff4e8, 1.5); light.position.set(3,4,5); scene.add(light)
    const fill = new DirectionalLight(0xc5deff, .45); fill.position.set(-3,1,-3); scene.add(fill)
    const box = new Box3().setFromObject(model), center = box.getCenter(new Vector3()), size = box.getSize(new Vector3())
    const max = Math.max(size.x, size.y, size.z), camera = new PerspectiveCamera(40, 1, max / 1000, max * 100)
    const orbit = new OrbitControls(camera, renderer.domElement); orbit.target.copy(center); orbit.enableDamping = true; orbit.minDistance = max * .3; orbit.maxDistance = max * 12
    const fit = (view: View = 'all') => {
      const vertical = camera.fov * Math.PI / 360, horizontal = Math.atan(Math.tan(vertical) * camera.aspect)
      const framing = box.clone()
      if (isPerson && view !== 'all' && view !== 'back') {
        const [low, high, breadth] = view === 'face' ? [.80, 1, .38] : view === 'shoes' ? [0, .20, .85] : [.38, .84, 1]
        framing.min.y = box.min.y + size.y * low; framing.max.y = box.min.y + size.y * high
        framing.min.x = center.x - size.x * breadth / 2; framing.max.x = center.x + size.x * breadth / 2
      }
      const target = framing.getCenter(new Vector3()), direction = new Vector3(view === 'face' ? .12 : .55, view === 'shoes' ? .7 : .18, view === 'back' ? -1.7 : 1.7).normalize()
      const right = new Vector3(0, 1, 0).cross(direction).normalize(), up = direction.clone().cross(right).normalize()
      let distance = 0
      for (const x of [framing.min.x, framing.max.x]) for (const y of [framing.min.y, framing.max.y]) for (const z of [framing.min.z, framing.max.z]) {
        const offset = new Vector3(x,y,z).sub(target)
        distance = Math.max(distance, Math.abs(offset.dot(right)) / Math.tan(horizontal) + offset.dot(direction), Math.abs(offset.dot(up)) / Math.tan(vertical) + offset.dot(direction))
      }
      orbit.minDistance = max * .08
      orbit.target.copy(target); camera.position.copy(target).add(direction.multiplyScalar(distance * 1.12)); orbit.update()
    }
    fitView.current = fit
    let framed = false
    const resize = () => { const width = element.clientWidth, height = element.clientHeight; if (!width || !height) return; renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix(); if (!framed) { fit(); framed = true } }
    resize(); const observer = new ResizeObserver(resize); observer.observe(element)
    renderer.setAnimationLoop(() => { orbit.update(); renderer.render(scene, camera) })
    return () => { observer.disconnect(); renderer.setAnimationLoop(null); orbit.dispose(); environment.dispose(); renderer.dispose(); renderer.domElement.remove(); fitView.current = null; scene.remove(model) }
  }, [model])
  return <div className="ai-viewer-wrap"><div ref={host} className="ai-viewer" />{error && <p role="alert" className="studio-error">{error}</p>}<div className="ai-camera"><button onClick={() => fitView.current?.('all')}>Przywróć widok</button>{person && <div className="ai-view-details" aria-label="Zbliżenia figurki">{([['face','Twarz'],['clothes','Ubranie'],['shoes','Buty'],['back','Tył']] as const).map(([view,label]) => <button key={view} onClick={() => fitView.current?.(view)}>{label}</button>)}</div>}<span>Obróć palcem · przybliż dwoma</span></div></div>
}
