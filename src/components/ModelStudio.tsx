import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import type { Group } from 'three'
import { api, followJob, modelBytes, savedJob, saveJob, type Job } from '../studio/generation'
import type { Adjustments } from '../studio/aiModel'
import { useDictation } from '../studio/useDictation'
import { ParametricModelStudio } from './ParametricModelStudio'
import '../studio/studio.css'
import '../studio/aiStudio.css'

const Viewer = lazy(() => import('./AiModelViewer'))
type Engine = typeof import('../studio/aiModel')
const defaults: Adjustments = { dimensions: ['', '', ''], angles: ['', '', ''] }
export function ModelStudio() {
  const [mode, setMode] = useState<'ai' | 'local'>('ai')
  const [prompt, setPrompt] = useState(''), [textures, setTextures] = useState(true)
  const [key, setKey] = useState(''), [connected, setConnected] = useState(false), [configured, setConfigured] = useState(false), [checking, setChecking] = useState(false)
  const [connectionOpen, setConnectionOpen] = useState(false), [connectionError, setConnectionError] = useState('')
  const [busy, setBusy] = useState(false), [note, setNote] = useState(''), [error, setError] = useState(''), [progress, setProgress] = useState(0)
  const [job, setJob] = useState<Job | null>(savedJob), [resultJob, setResultJob] = useState<Job | null>(null)
  const [source, setSource] = useState<Group | null>(null), [model, setModel] = useState<Group | null>(null), [size, setSize] = useState<number[]>([])
  const [adjustments, setAdjustments] = useState<Adjustments>(defaults), [adjustmentError, setAdjustmentError] = useState(''), [exporting, setExporting] = useState(false)
  const engine = useRef<Engine | null>(null), operation = useRef<AbortController | null>(null), sourceRef = useRef<Group | null>(null)
  const speech = useDictation(text => setPrompt(text))
  useEffect(() => {
    const controller = new AbortController()
    api<{ configured: boolean }>('config', '', controller.signal).then(config => { setConfigured(config.configured); setConnected(config.configured) }).catch(() => { /* Generation reports service errors on action. */ })
    return () => { controller.abort(); operation.current?.abort(); if (sourceRef.current) engine.current?.disposeModel(sourceRef.current) }
  }, [])
  useEffect(() => {
    if (!source || !engine.current) return
    try { const next = engine.current.transformModel(source, adjustments); setModel(next); setSize(engine.current.modelSize(next)); setAdjustmentError('') } catch (e) { setAdjustmentError((e as Error).message) }
  }, [source, adjustments])
  function remember(next: Job) { setJob(next); saveJob(next) }
  async function verify() {
    setChecking(true); setConnectionError('')
    try { await api('verify', key); setConnected(true); setConnectionOpen(false) } catch (e) { setConnected(false); setConnectionError((e as Error).message) } finally { setChecking(false) }
  }
  async function run(resume?: Job, previewOnly = false) {
    if (operation.current) return
    if (!connected) { setConnectionOpen(true); setError('Aby tworzyć modele z dowolnego opisu, najpierw podłącz konto Meshy poniżej.'); return }
    if (!resume && (!prompt.trim() || prompt.length > 800)) { setError('Wpisz opis od 1 do 800 znaków. Nie musisz podawać wymiarów.'); return }
    const controller = new AbortController(); operation.current = controller
    setBusy(true); setError(''); setProgress(0); setNote(resume ? 'Sprawdzam zapisane zadanie…' : 'Wysyłam opis do Meshy…')
    try {
      let current = resume
      if (!current) {
        const created = await api<{ id: string }>('tasks', key, controller.signal, { action: 'preview', prompt: prompt.trim() })
        current = { id: created.id, prompt: prompt.trim(), textured: textures, stage: 'preview' }; remember(current)
      }
      const completed = await followJob(previewOnly ? { ...current, textured: false } : current, key, controller.signal, (task, j) => {
        setProgress(task.progress); setNote((j.stage === 'preview' ? 'Tworzę geometrię' : 'Nakładam tekstury') + ` · ${task.progress}%`)
      }, remember)
      setNote('Pobieram model 3D…')
      const bytes = await modelBytes(completed.id, key, controller.signal)
      engine.current ??= await import('../studio/aiModel')
      const loaded = await engine.current.loadModel(bytes)
      if (controller.signal.aborted) { engine.current.disposeModel(loaded); return }
      if (sourceRef.current) engine.current.disposeModel(sourceRef.current)
      sourceRef.current = loaded; setSource(loaded); setResultJob(completed)
      setNote(completed.stage === 'refine' ? 'Gotowe — model z teksturami.' : 'Gotowe — geometria bez tekstur.'); setProgress(100)
    } catch (e) {
      if (controller.signal.aborted) setNote('Śledzenie wstrzymane. Zadanie może nadal działać w Meshy; wznowienie sprawdza jego wynik.')
      else { setError((e as Error).message); setNote('Model nie został zastąpiony. Możesz wznowić sprawdzanie zapisanego zadania.') }
    } finally { if (operation.current === controller) { operation.current = null; setBusy(false) } }
  }
  async function download(format: 'glb' | 'stl') {
    if (!model || !engine.current) return
    setExporting(true); setError('')
    try {
      const blob = await engine.current.exportModel(model, format), url = URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url; a.download = `froge-${resultJob?.id ?? 'model'}${format === 'stl' ? '-mm' : ''}.${format}`; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch { setError('Nie udało się wyeksportować modelu. Spróbuj ponownie.') } finally { setExporting(false) }
  }
  function field(group: 'dimensions' | 'angles', index: number, value: string) {
    setAdjustments(previous => { const next = { ...previous, [group]: [...previous[group]] as [string,string,string] }; next[group][index] = value; return next })
  }
  const tabs = <div className="ai-mode"><button aria-pressed={mode === 'ai'} onClick={() => setMode('ai')}>Model z opisu · AI</button><button aria-pressed={mode === 'local'} onClick={() => setMode('local')}>Bryły parametryczne</button></div>
  if (mode === 'local') return <>{tabs}<ParametricModelStudio /></>
  return <div className="model-studio ai-studio">
    {tabs}
    <header className="studio-intro"><div><p className="studio-eyebrow">FROGE / STUDIO MODELI 3D</p><h1>Powiedz, co tworzymy.</h1><p>Opisz obiekt. Wymiary i kąty możesz dodać później.</p></div></header>
    <div className="ai-layout">
      <section className="studio-panel studio-command" aria-label="Generowanie modelu z opisu">
        <label className="studio-prompt-label" htmlFor="ai-prompt">Co mam stworzyć?</label>
        <textarea id="ai-prompt" value={prompt} maxLength={800} rows={6} onChange={e => setPrompt(e.target.value)} placeholder="Np. rozłożysty dąb z grubym pniem, korzeniami i zielonymi liśćmi, realistyczna kora…" />
        <div className="ai-prompt-meta"><span>Dowolny opis obiektu</span><span>{prompt.length}/800</span></div>
        <div className="studio-examples">{['Drzewo dąb z liśćmi i korzeniami', 'Figurka smoka z rozłożonymi skrzydłami', 'Rakieta kosmiczna z oknem'].map(text => <button key={text} onClick={() => setPrompt(text)}>{text}</button>)}</div>
        <label className="studio-switch"><input type="checkbox" checked={textures} onChange={e => setTextures(e.target.checked)} />Dodaj tekstury</label>
        <button className="studio-primary" disabled={busy || !prompt.trim()} onClick={() => void run()}>{busy ? 'Generowanie w toku…' : 'Generuj model 3D'} <span>↗</span></button>
        <p className="studio-helper">Generacja używa kredytów API Meshy i może potrwać kilka minut. Pisanie i dyktowanie zmieniają opis; przycisk rozpoczyna nowe zadanie.</p>
        <button className={speech.listening ? 'studio-mic is-listening' : 'studio-mic'} aria-pressed={speech.listening} disabled={!speech.supported} onClick={speech.listening ? speech.stop : speech.start}>{speech.listening ? 'Zatrzymaj dyktowanie' : 'Dyktuj opis'}</button>
        <small className="studio-helper">{speech.supported ? 'Mikrofon włącza się po kliknięciu. Rozpoznawanie mowy korzysta z usługi przeglądarki.' : 'Możesz podyktować opis mikrofonem klawiatury telefonu.'}</small>
        {speech.interim && <p>{speech.interim}</p>}{speech.error && <p role="alert" className="studio-error">{speech.error}</p>}
        <details className="ai-connection" open={connectionOpen} onToggle={e => setConnectionOpen(e.currentTarget.open)}><summary>Połączenie AI · {connected ? (configured ? 'skonfigurowane' : 'sprawdzone') : 'wymaga podłączenia'}</summary>
          <p>Podłącz klucz API z konta Meshy. Opis i klucz są przesyłane do Meshy przez tę stronę. Klucz wpisany tutaj pozostaje tylko w pamięci karty.</p>
          <a href="https://www.meshy.ai/settings/api" target="_blank" rel="noreferrer">Otwórz ustawienia API Meshy ↗</a>
          <label className="studio-field">Klucz API Meshy<input type="password" value={key} autoComplete="off" spellCheck={false} placeholder={configured ? 'Używany jest klucz serwera' : 'Wklej klucz API tutaj'} onChange={e => { setKey(e.target.value); setConnected(false) }} /></label>
          <button disabled={checking || (!key.trim() && !configured)} onClick={() => void verify()}>{checking ? 'Sprawdzam…' : 'Sprawdź połączenie'}</button>
          {connectionError && <p role="alert" className="studio-error">{connectionError}</p>}
        </details>
        {(busy || note) && <div className="ai-progress" role="status"><p>{note}</p>{busy && <progress max={100} value={progress} aria-label="Postęp bieżącego etapu" />}</div>}
        {busy && <button onClick={() => operation.current?.abort()}>Wstrzymaj śledzenie</button>}
        {error && <p role="alert" className="studio-error">{error}</p>}
        {job && !busy && <div className="ai-resume"><button onClick={() => void run(job)}>Sprawdź zapisane zadanie</button>{(job.previewId || job.stage === 'preview') && <button onClick={() => void run({ ...job, id: job.previewId || job.id, stage: 'preview' }, true)}>Pobierz samą geometrię</button>}<small>Zadanie: {job.id}</small></div>}
      </section>
      <section className="studio-canvas-panel" aria-label="Wynik generowania">
        <div className="studio-canvas-heading"><div><small>{resultJob ? 'TWÓJ MODEL' : 'OBSZAR ROBOCZY'}</small><h2>{resultJob?.prompt || 'Tu pojawi się Twój model'}</h2></div></div>
        {model ? <Suspense fallback={<p className="ai-empty">Ładuję podgląd…</p>}><Viewer model={model} /></Suspense> : <div className="ai-empty"><b>{busy ? 'Trwa tworzenie modelu' : 'Zacznij od pomysłu'}</b><p>{busy ? 'Po zakończeniu zobaczysz tutaj przestrzenną geometrię.' : 'Drzewo, figurka, pojazd lub część. Wpisz opis po lewej i kliknij „Generuj model 3D”.'}</p>{!connected && <button onClick={() => setConnectionOpen(true)}>Podłącz generator AI</button>}</div>}
        {model && <><div className="studio-measures">{['SZEROKOŚĆ X', 'WYSOKOŚĆ Y', 'GŁĘBOKOŚĆ Z'].map((label, i) => <div key={label}><small>{label}</small><b>{size[i]?.toFixed(2)} <span>cm</span></b></div>)}</div><div className="studio-export"><p>{resultJob?.stage === 'refine' ? 'Model zawiera tekstury.' : 'Podgląd geometrii — bez tekstur.'} Eksport uwzględnia widoczną skalę i obrót.</p><div className="studio-export-buttons"><button disabled={exporting || !!adjustmentError} onClick={() => void download('glb')}>Pobierz GLB</button><button disabled={exporting || !!adjustmentError} onClick={() => void download('stl')}>Pobierz STL · mm</button></div><p>STL nie zawiera tekstur. Model AI wymaga sprawdzenia i ewentualnej naprawy przed drukiem lub użyciem jako część techniczna.</p></div></>}
        <details className="ai-adjustments"><summary>Wymiary i kąty · opcjonalnie</summary><p>Zostaw puste, aby zachować proporcje. Domyślnie najdłuższy bok ma 10 cm. Jeden wymiar skaluje całość proporcjonalnie; kilka wymiarów może zmienić proporcje.</p><div className="ai-fields">{['Szerokość X', 'Wysokość Y', 'Głębokość Z'].map((label,i) => <label key={label}>{label} · cm<input type="number" min="0.1" max="1000" step="0.1" placeholder="Automatycznie" value={adjustments.dimensions[i]} onChange={e => field('dimensions', i, e.target.value)} /></label>)}</div><p>Kąty obrotu modelu (nie kąty konstrukcyjne). Wymiary powyżej dotyczą obiektu przed obrotem.</p><div className="ai-fields">{['X','Y','Z'].map((label,i) => <label key={label}>Obrót {label} · °<input type="number" min="-360" max="360" placeholder="0" value={adjustments.angles[i]} onChange={e => field('angles',i,e.target.value)} /></label>)}</div><button onClick={() => setAdjustments(defaults)}>Wyczyść ustawienia</button>{adjustmentError && <p role="alert" className="studio-error">{adjustmentError} Podgląd zachowuje ostatnią poprawną skalę.</p>}</details>
      </section>
    </div>
    <footer className="studio-footer"><span>FROGE MPC 2 · Studio 3D</span><Link to="/contest">Fundament konkursowy →</Link><Link to="/shop-lab">Laboratorium ofert →</Link></footer>
  </div>
}
