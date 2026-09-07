import { lazy, Suspense, useEffect, useRef, useState, useSyncExternalStore } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { newProduct } from '../commerce/domain'
import { commerceRequest } from '../commerce/client'
import type { Group } from 'three'
import { sceneModel, sceneSchema, type ModelScene } from '../studio/scene'
import { getAgentScene, subscribeAgentScene, requestAgentModel, invalidateAgentRequest } from '../studio/agentSceneStore'
import type { Adjustments } from '../studio/aiModel'
import { useDictation } from '../studio/useDictation'
import { ParametricModelStudio } from './ParametricModelStudio'
import { RemoteGenerator } from '../blender/RemoteGenerator'
import { PlannedMarketplaces } from './PlannedMarketplaces'
import type { GenerationJob } from '../blender/client'
import '../studio/studio.css'
import '../studio/aiStudio.css'

const Viewer = lazy(() => import('./AiModelViewer'))
type Engine = typeof import('../studio/aiModel')
const defaults: Adjustments = { dimensions: ['', '', ''], angles: ['', '', ''] }
export function ModelStudio() {
  const navigate=useNavigate()
  const [mode, setMode] = useState<'ai' | 'local'>('ai')
  const [prompt,setPrompt]=useState(''),[name,setName]=useState(''),[sceneData,setSceneData]=useState<ModelScene|null>(null)
  const [busy,setBusy]=useState(false),[note,setNote]=useState(''),[error,setError]=useState('')
  const [source,setSource]=useState<Group|null>(null),[model,setModel]=useState<Group|null>(null),[size,setSize]=useState<number[]>([])
  const [adjustments,setAdjustments]=useState<Adjustments>(defaults),[adjustmentError,setAdjustmentError]=useState(''),[exporting,setExporting]=useState(false)
  const engine=useRef<Engine|null>(null),sourceRef=useRef<Group|null>(null),loadRevision=useRef(0)
  const agent=useSyncExternalStore(subscribeAgentScene,getAgentScene)
  const speech=useDictation(text=>setPrompt(text))
  useEffect(()=>()=>{loadRevision.current++;if(sourceRef.current)engine.current?.disposeModel(sourceRef.current)},[])
  useEffect(()=>{if(agent.scene)void showScene(agent.scene,'Agent dostarczył model: '+agent.scene.name)},[agent.scene])
  useEffect(()=>{if(!source||!engine.current)return;try{const next=engine.current.transformModel(source,adjustments);setModel(next);setSize(engine.current.modelSize(next));setAdjustmentError('')}catch(e){setAdjustmentError((e as Error).message)}},[source,adjustments])
  function prepareRequest() {
    try { requestAgentModel(prompt); setError(''); setNote('Polecenie czeka na agenta. Samo kliknięcie nie uruchamia Codexa ani Blendera.'); } catch (e) { setError((e as Error).message) }
  }
  function startRemote() {
    invalidateAgentRequest()
    setError(''); setNote('Podgląd zachowuje poprzedni model, dopóki nowy wynik nie zostanie wczytany.')
    return ++loadRevision.current
  }
  async function receiveRemote(bytes: ArrayBuffer, job: GenerationJob, revision: number): Promise<boolean> {
    return loadGlb(bytes, job.prompt.slice(0,120), 'Wczytano model utworzony przez Blender na Twoim serwerze. Możesz go obracać, pobrać lub dodać do katalogu.', revision)
  }
  async function loadGlb(bytes: ArrayBuffer, label: string, message: string, revision: number): Promise<boolean> {
    if (revision !== loadRevision.current) return false
    setBusy(true)
    let loaded: Group | null = null
    try {
      engine.current ??= await import('../studio/aiModel')
      loaded = await engine.current.loadModel(bytes)
      engine.current.transformModel(loaded, defaults)
      if (revision !== loadRevision.current) { engine.current.disposeModel(loaded); return false }
      if (sourceRef.current) engine.current.disposeModel(sourceRef.current)
      sourceRef.current = loaded
      setSource(loaded); setSceneData(null); setAdjustments(defaults)
      setName(label); setNote(message)
      return true
    } catch (e) {
      if (loaded && loaded !== sourceRef.current) engine.current?.disposeModel(loaded)
      if (revision === loadRevision.current) setError((e as Error).message)
      throw e
    } finally { if (revision === loadRevision.current) setBusy(false) }
  }
  async function showScene(value: unknown, label: string) {
    const revision=++loadRevision.current
    setBusy(true); setError('')
    try {
      const scene = sceneSchema.parse(value)
      engine.current ??= await import('../studio/aiModel')
      const loaded = sceneModel(scene)
      try {engine.current.transformModel(loaded, defaults)}catch(e){engine.current.disposeModel(loaded);throw e}
      if(revision!==loadRevision.current){engine.current.disposeModel(loaded);return}
      if (sourceRef.current) engine.current.disposeModel(sourceRef.current)
      sourceRef.current = loaded; setSource(loaded); setSceneData(scene); setName(scene.name); setNote(label)
    } catch (e) { setError('Nie udało się wczytać sceny: ' + (e as Error).message) } finally { setBusy(false) }
  }
  async function example() {
    ++loadRevision.current
    invalidateAgentRequest()
    setBusy(true);setError('')
    try { const response = await fetch('/models/codex-dragon.froge.json'); if (!response.ok) throw new Error('Plik modelu niedostępny.'); await showScene(await response.json(), 'Gotowy projekt smoka przygotowany przez Codexa. To przykład, nie wynik wpisanego właśnie opisu.') } catch (e) { setError((e as Error).message); setBusy(false) }
  }
  async function rapperExample() {
    const revision=++loadRevision.current
    invalidateAgentRequest();setBusy(true);setError('')
    try {
      const response=await fetch('/models/rapper-v10.glb')
      if(!response.ok)throw new Error('Przykład figurki jest chwilowo niedostępny.')
      await loadGlb(await response.arrayBuffer(),'Raper · styl lat 2000','Przykład inspirowany stylem Eminema: krótka fryzura, luźna koszulka, denim i sneakersy. Twarz jest przykładowa, nie jest portretem artysty.',revision)
    } catch(e) { if(revision===loadRevision.current)setError((e as Error).message) }
    finally { if(revision===loadRevision.current)setBusy(false) }
  }
  async function importFile(file?: File) {
    if (!file) return
    const revision = ++loadRevision.current
    invalidateAgentRequest()
    if (file.size > 64 * 1024 * 1024) {setError('Maksymalny rozmiar pliku to 64 MB.');return}
    if (file.name.toLowerCase().endsWith('.json')) {try {if(file.size>16*1024*1024)throw new Error('Limit sceny JSON to 16 MB.');await showScene(JSON.parse(await file.text()),'Wczytano scenę do dalszej edycji.')}catch(e){setError((e as Error).message)};return}
    setBusy(true);setError('')
    try {engine.current ??= await import('../studio/aiModel');const loaded=await engine.current.loadModel(await file.arrayBuffer());engine.current.transformModel(loaded,defaults);if(revision!==loadRevision.current){engine.current.disposeModel(loaded);return}if(sourceRef.current)engine.current.disposeModel(sourceRef.current);sourceRef.current=loaded;setSource(loaded);setSceneData(null);setName(file.name);setNote('Wczytano model GLB. Możesz go skalować i eksportować.')}catch(e){if(revision===loadRevision.current)setError((e as Error).message)}finally{if(revision===loadRevision.current)setBusy(false)}
  }
  function saveJson(filename: string, value: unknown) {
    const url=URL.createObjectURL(new Blob([JSON.stringify(value)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)
  }
  async function copyRequest() {
    const text='Wykonaj dla mnie model 3D: '+prompt+'\nDostarcz GLB z materiałami albo scenę Froge JSON do importu. Jeżeli masz dostęp do WebMCP tej strony, odczytaj get_3d_modeling_request i get_3d_scene_schema, a wynik zastosuj przez apply_3d_model_scene. Nie zastępuj opisu niepasującym presetem.'
    try {await navigator.clipboard.writeText(text);setNote('Skopiowano. Wklej polecenie w rozmowie z Codexem.')}catch{setError('Schowek jest niedostępny. Zaznacz opis i skopiuj go ręcznie.')}
  }
  async function download(format: 'glb' | 'stl') {
    if (!model || !engine.current) return
    setExporting(true); setError('')
    try {
      const blob = await engine.current.exportModel(model, format), url = URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url; a.download = `froge-model${format === 'stl' ? '-mm' : ''}.${format}`; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch { setError('Nie udało się wyeksportować modelu. Spróbuj ponownie.') } finally { setExporting(false) }
  }
  function field(group: 'dimensions' | 'angles', index: number, value: string) {
    setAdjustments(previous => { const next = { ...previous, [group]: [...previous[group]] as [string,string,string] }; next[group][index] = value; return next })
  }
  async function saveProduct() {
    if(!model||!engine.current||exporting)return
    setExporting(true);setError('')
    try {
      const blob=await engine.current.exportModel(model,'glb')
      if(blob.size>12*1024*1024)throw new Error('Model przekracza limit katalogu 12 MB. Pobierz go i przygotuj lżejszą wersję.')
      const asset=await commerceRequest('models',{method:'POST',headers:{'Content-Type':'model/gltf-binary'},body:blob})
      const product={...newProduct(),title:(name||'Mój model 3D').slice(0,160),description:sceneData?.description||'',variant:size.map(n=>n.toFixed(2)).join(' × ')+' cm',modelFile:asset.filename}
      await commerceRequest('products',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({product,revision:0})})
      navigate('/shop?product='+product.id)
    }catch(e){setError((e as Error).message)}finally{setExporting(false)}
  }
  const tabs = <div className="ai-mode"><button aria-pressed={mode === 'ai'} onClick={() => setMode('ai')}>AI + Blender</button><button aria-pressed={mode === 'local'} onClick={() => setMode('local')}>Bryły parametryczne</button></div>
  if (mode === 'local') return <>{tabs}<ParametricModelStudio /></>
  return <div className="model-studio ai-studio">
    {tabs}
    <header className="studio-intro"><div><p className="studio-eyebrow">FROGE / STUDIO MODELI 3D</p><h1>Powiedz, co tworzymy.</h1><p>Opisz obiekt. Wymiary i kąty możesz dodać później.</p></div></header>
    <div className="ai-layout">
      <section className="studio-panel studio-command" aria-label="Generowanie modelu z opisu">
        <label className="studio-prompt-label" htmlFor="ai-prompt">Co mam stworzyć?</label>
        <textarea id="ai-prompt" value={prompt} maxLength={2000} rows={5} onChange={e=>setPrompt(e.target.value)} placeholder="Np. figurka zielonego smoka z rogami, wąsami i łuskami…" />
        <div className="ai-prompt-meta"><span>Bez wymaganych wymiarów</span><span>{prompt.length}/2000</span></div>
        <RemoteGenerator prompt={prompt} onStart={startRemote} onResult={receiveRemote}/>
        <details className="agent-manual"><summary>Praca z Codexem przez WebMCP</summary>
          <p className="studio-helper">Możesz też przekazać opis agentowi Codex, który dostarczy geometrię do tej strony. Ten tryb wymaga osobnego polecenia w rozmowie.</p>
          <button disabled={!prompt.trim()} onClick={prepareRequest}>Przygotuj polecenie dla agenta</button>
          {agent.request && <div className="ai-resume"><button onClick={()=>void copyRequest()}>Kopiuj polecenie do Codexa</button><button onClick={()=>saveJson('polecenie-blender.json',{type:'froge-modeling-request',version:1,prompt:agent.request!.prompt})}>Pobierz polecenie do Blendera</button></div>}
        </details>
        <button className={speech.listening?'studio-mic is-listening':'studio-mic'} aria-pressed={speech.listening} disabled={!speech.supported} onClick={speech.listening?speech.stop:speech.start}>{speech.listening?'Zatrzymaj dyktowanie':'Dyktuj opis'}</button>
        <small className="studio-helper">{speech.supported?'Dyktowanie wpisuje tekst. Mikrofon włącza się po kliknięciu i korzysta z usługi przeglądarki.':'Możesz użyć mikrofonu klawiatury telefonu.'}</small>
        {speech.interim && <p>{speech.interim}</p>}{speech.error && <p role="alert" className="studio-error">{speech.error}</p>}
        <div className="blender-addon"><h2>Blender · darmowy warsztat 3D</h2><p>Wczytaj model od Codexa albo generuj z opisu przez lokalne Ollama na komputerze. Dodatek tworzy edytowalne części i tekstury, bez płatnego API.</p><a className="blender-download" href="/downloads/froge-blender-addon.zip" download>Pobierz dodatek do Blendera ↓</a><details><summary>Jak uruchomić na komputerze?</summary><ol><li>Zainstaluj <a href="https://www.blender.org/download/" target="_blank" rel="noreferrer">Blendera</a> (4.2 lub nowszy).</li><li>W Preferences → Add-ons → Install from Disk wybierz pobrany ZIP i włącz Froge Studio.</li><li>W widoku 3D naciśnij N i otwórz zakładkę Froge. Wczytaj scenę JSON z tej strony.</li><li>Opcjonalne generowanie z opisu: zainstaluj <a href="https://ollama.com/download" target="_blank" rel="noreferrer">Ollama</a> i lokalny model odpowiedni do Twojego komputera. W dodatku kliknij „Sprawdź lokalne modele”, wpisz opis i „Generuj lokalnie”.</li><li>Wyeksportuj GLB i wczytaj go tutaj. Projekt Blendera zapiszesz przez File → Save As.</li></ol><p>Blender działa na komputerze. Ta strona na telefonie nie uruchomi go sama. Lokalny model AI jest osobny od Codexa; jakość zależy od modelu i sprzętu.</p><a href="/downloads/BLENDER-INSTRUKCJA.txt" download>Pobierz instrukcję</a></details></div>
        {(note||agent.status==='waiting') && <div className="ai-progress" role="status"><p>{agent.status==='waiting'?agent.note:note}</p></div>}
        {error && <p role="alert" className="studio-error">{error}</p>}
      </section>
      <section className="studio-canvas-panel" aria-label="Wynik generowania">
        <div className="studio-canvas-heading"><div><small>{model?'TWÓJ MODEL':'OBSZAR ROBOCZY'}</small><h2>{name||'Twój model 3D'}</h2></div></div>
        {model?<Suspense fallback={<p className="ai-empty">Ładuję podgląd…</p>}><Viewer model={model}/></Suspense>:<div className="ai-empty"><b>{busy?'Wczytuję geometrię…':'Tutaj pojawi się Twój model'}</b><p>Połącz serwer, opisz obiekt i kliknij „Generuj model 3D”. Gotowy wynik pojawi się tutaj automatycznie.</p><button disabled={busy} onClick={()=>void example()}>Obejrzyj przykład · smok</button></div>}
        <div className="studio-export"><div className="studio-export-buttons"><button disabled={busy} onClick={()=>void rapperExample()}>Przykład · raper</button><button disabled={busy} onClick={()=>void example()}>Przykład · smok Codexa</button><label className="blender-import">Wczytaj GLB lub scenę JSON<input aria-label="Wczytaj model GLB lub JSON" type="file" accept=".glb,.json" disabled={busy} onChange={e=>{void importFile(e.target.files?.[0]);e.target.value=''}}/></label></div></div>
        {model && <><div className="studio-measures">{['SZEROKOŚĆ X','WYSOKOŚĆ Y','GŁĘBOKOŚĆ Z'].map((label,i)=><div key={label}><small>{label}</small><b>{size[i]?.toFixed(2)} <span>cm</span></b></div>)}</div><div className="studio-export"><p>GLB zachowuje materiały i tekstury. Eksport GLB/STL uwzględnia widoczną skalę i obrót.</p><div className="studio-export-buttons"><button disabled={exporting||busy||!!adjustmentError} onClick={()=>void saveProduct()}>Dodaj model do katalogu</button><button disabled={exporting||!!adjustmentError} onClick={()=>void download('glb')}>Pobierz GLB + tekstury</button><button disabled={exporting||!!adjustmentError} onClick={()=>void download('stl')}>Pobierz STL · mm</button>{sceneData && <button onClick={()=>saveJson('model-blender.froge.json',sceneData)}>Scena do dodatku Blender · JSON</button>}</div><p>JSON zachowuje części w źródłowej skali, przed zmianami wymiarów i obrotów. STL nie zawiera tekstur. Przed drukiem sprawdź siatkę i połącz przecinające się części.</p></div></>}
        <details className="ai-adjustments"><summary>Wymiary i kąty · opcjonalnie</summary><p>Zostaw puste, aby zachować proporcje. Domyślnie najdłuższy bok ma 10 cm. Jeden wymiar skaluje całość proporcjonalnie; kilka wymiarów może zmienić proporcje.</p><div className="ai-fields">{['Szerokość X', 'Wysokość Y', 'Głębokość Z'].map((label,i) => <label key={label}>{label} · cm<input type="number" min="0.1" max="1000" step="0.1" placeholder="Automatycznie" value={adjustments.dimensions[i]} onChange={e => field('dimensions', i, e.target.value)} /></label>)}</div><p>Kąty obrotu modelu (nie kąty konstrukcyjne). Wymiary powyżej dotyczą obiektu przed obrotem.</p><div className="ai-fields">{['X','Y','Z'].map((label,i) => <label key={label}>Obrót {label} · °<input type="number" min="-360" max="360" placeholder="0" value={adjustments.angles[i]} onChange={e => field('angles',i,e.target.value)} /></label>)}</div><button onClick={() => setAdjustments(defaults)}>Wyczyść ustawienia</button>{adjustmentError && <p role="alert" className="studio-error">{adjustmentError} Podgląd zachowuje ostatnią poprawną skalę.</p>}</details>
      </section>
    </div>
    <PlannedMarketplaces />
    <footer className="studio-footer"><span>FROGE MPC 2 · Studio 3D</span><Link to="/contest">Fundament konkursowy →</Link><Link to="/shop">Katalog i kanały sprzedaży →</Link></footer>
  </div>
}
