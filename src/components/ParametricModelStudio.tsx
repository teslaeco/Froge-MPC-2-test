import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react'
import { Link } from 'react-router-dom'
import { EnhancedProceduralAssetViewer, type ViewerAsset } from './EnhancedProceduralAssetViewer'
import { base64, createModel, exportStl, INITIAL_PROMPT, INITIAL_SPEC, SHAPE_NAMES, type ModelSpec } from '../studio/model'
import { applyStudioCommand, getStudio, subscribeStudio, undoStudio, updateStudio } from '../studio/store'
import { useDictation } from '../studio/useDictation'
import '../studio/studio.css'

function save(name: string, data: string | Uint8Array, type: string) {
  const url = URL.createObjectURL(new Blob([typeof data === 'string' ? data : Uint8Array.from(data)], { type }))
  const a = document.createElement('a'); a.href = url; a.download = name; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000)
}
function NumberField({ label, value, min, max, step = 1, suffix, onChange }: { label: string; value: number; min: number; max: number; step?: number; suffix: string; onChange: (v: number) => void }) {
  const [draft, setDraft] = useState(String(value))
  useEffect(() => { setDraft(String(value)) }, [value])
  return <label className="studio-field">{label}<span><input aria-label={label} type="number" value={draft} min={min} max={max} step={step} onChange={e => { setDraft(e.target.value); if (e.target.value !== '' && Number.isFinite(e.target.valueAsNumber)) onChange(e.target.valueAsNumber) }} onBlur={() => setDraft(String(value))} /><small>{suffix}</small></span></label>
}
export function ParametricModelStudio() {
  const state = useSyncExternalStore(subscribeStudio, getStudio), { spec } = state
  const [prompt, setPrompt] = useState(INITIAL_PROMPT), [live, setLive] = useState(false), [unit, setUnit] = useState<'mm' | 'cm'>('cm')
  const [exportError, setExportError] = useState('')
  const lastApplied = useRef('')
  const speech = useDictation(text => setPrompt(text))
  useEffect(() => {
    if (!live || !prompt.trim() || prompt === lastApplied.current) return
    const timer = setTimeout(() => { lastApplied.current = prompt; applyStudioCommand(prompt) }, 650)
    return () => clearTimeout(timer)
  }, [prompt, live])
  const model = useMemo(() => createModel(spec), [spec])
  const bundle = useMemo<ViewerAsset>(() => ({ geometryFingerprint: model.id, semanticParts: [], preview: { ...model.mesh, preset: spec.shape, label: SHAPE_NAMES[spec.shape], promptMatched: true, primaryColor: spec.color, secondaryColor: spec.accent, textureOnly: true }, texture: { bytes: model.texture, mimeType: 'image/png', fingerprint: model.id } }), [model, spec])
  const scale = unit === 'cm' ? 10 : 1
  function change(patch: Partial<ModelSpec>) {
    const next = { ...spec, ...patch }
    if (next.shape === 'sphere') next.height = next.diameter = patch.height ?? next.diameter
    updateStudio(next, 'Parametry zaktualizowane. Podgląd i eksport pokazują tę samą wersję.')
  }
  function download(kind: 'gltf' | 'stl' | 'png' | 'json') {
    try {
      const filename = `${spec.shape}-${model.id}`
      if (kind === 'gltf') save(filename + '.gltf', JSON.stringify(model.gltf), 'model/gltf+json')
      if (kind === 'stl') save(filename + '-mm.stl', exportStl(model.mesh), 'model/stl')
      if (kind === 'png') save(filename + '-texture.png', model.texture, 'image/png')
      if (kind === 'json') save(filename + '-spec.json', JSON.stringify({ spec, qa: model.qa, revision: state.revision, version: model.id, llmUsed: false }, null, 2), 'application/json')
      setExportError('')
    } catch { setExportError('Nie udało się zapisać pliku. Spróbuj ponownie.') }
  }
  return <div className="model-studio">
    <header className="studio-intro"><div><p className="studio-eyebrow">FROGE / STUDIO MODELI 3D</p><h1>Powiedz, co tworzymy.</h1><p>Od pomysłu do modelu. Dopasuj każdy milimetr.</p></div><div className="studio-version"><span className="studio-dot" />Podgląd na żywo <small>Wersja {state.revision.toString().padStart(2, '0')}</small></div></header>
    <div className="studio-layout">
      <section className="studio-panel studio-command" aria-labelledby="command-heading">
        <div className="studio-panel-heading"><span>01</span><h2 id="command-heading">Polecenie dla agenta</h2></div>
        <div className="studio-agent-note"><strong>Asystent parametrów</strong><p>Rakieta, walec, stożek i kula. Zmieniaj wymiary, kolor, teksturę, okno i lotki.</p><small>Tryb lokalny · swobodne AI niepodłączone</small></div>
        <label className="studio-prompt-label" htmlFor="studio-prompt">Co mam stworzyć lub zmienić?</label>
        <textarea id="studio-prompt" rows={6} maxLength={2000} value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Np. rakieta o średnicy 1 cm i wysokości 5 cm…" />
        <button className="studio-primary" onClick={() => { lastApplied.current = prompt; applyStudioCommand(prompt) }}>Zastosuj polecenie <span>↗</span></button>
        <label className="studio-switch"><input type="checkbox" checked={live} onChange={e => setLive(e.target.checked)} />Wprowadzaj polecenia na żywo</label>
        <small className="studio-helper">Po krótkiej przerwie w pisaniu lub zakończonym zdaniu z mikrofonu. Wymiary w panelu aktualizują się od razu.</small>
        <button className={speech.listening ? 'studio-mic is-listening' : 'studio-mic'} aria-pressed={speech.listening} disabled={!speech.supported} onClick={speech.listening ? speech.stop : speech.start}>{speech.listening ? '■ Zatrzymaj mikrofon' : '◉ Dyktuj polecenie'}</button>
        <small className="studio-helper">{speech.supported ? 'Mikrofon włącza się po kliknięciu. Rozpoznawanie mowy może przesyłać dźwięk do usługi przeglądarki.' : 'Dyktowanie niedostępne w tej przeglądarce. Możesz użyć mikrofonu klawiatury telefonu.'}</small>
        {speech.interim && <p className="studio-transcript">{speech.interim}</p>}{speech.error && <p role="alert" className="studio-error">{speech.error}</p>}
        <div className="studio-examples"><span>WYPRÓBUJ POLECENIE</span>{['Wysokość 6 cm', 'Kolor niebieski', 'Dodaj lotki', 'Bez okna'].map(text => <button key={text} onClick={() => { setPrompt(text); lastApplied.current = text; applyStudioCommand(text) }}>{text} ↗</button>)}</div>
        <div className="studio-feedback" role="status">{state.note}</div>
        {state.errors.length > 0 && <div role="alert" className="studio-error"><b>Model zachowuje poprzednią wersję.</b>{state.errors.map((e,i) => <p key={i}>{e}</p>)}</div>}
      </section>

      <section className="studio-canvas-panel" aria-label="Model 3D i eksport">
        <div className="studio-canvas-heading"><div><small>OBSZAR ROBOCZY</small><h2>{SHAPE_NAMES[spec.shape]}</h2></div><button disabled={!state.history.length} onClick={undoStudio}>↶ Cofnij</button></div>
        <EnhancedProceduralAssetViewer bundle={bundle} studio />
        <div className="studio-measures"><div><small>SZEROKOŚĆ X</small><b>{(model.qa.sizeMm[0]/scale).toFixed(2)} <span>{unit}</span></b></div><div><small>WYSOKOŚĆ Y</small><b>{(model.qa.sizeMm[1]/scale).toFixed(2)} <span>{unit}</span></b></div><div><small>GŁĘBOKOŚĆ Z</small><b>{(model.qa.sizeMm[2]/scale).toFixed(2)} <span>{unit}</span></b></div></div>
        <div className="studio-export"><div><h3>Twój model. Twoje pliki.</h3><p>glTF zawiera teksturę. STL to geometria w mm, bez kolorów.</p></div><div className="studio-export-buttons"><button onClick={() => download('gltf')}>↓ Model + tekstura</button><button onClick={() => download('stl')}>↓ STL</button><button onClick={() => download('json')}>↓ Wymiary / JSON</button></div></div>
        {exportError && <p role="alert">{exportError}</p>}
        <div className="studio-statusline"><span>● Geometria wygenerowana</span><span>{(model.mesh.indices.length/3).toLocaleString('pl-PL')} trójkątów</span><span>Eksport = podgląd</span></div>
        <p className="studio-manufacturing">Model parametryczny do oceny. Przydatność do druku wymaga kontroli wykonawcy.{spec.fins && spec.shape === 'rocket' ? ' Lotki zwiększają gabaryt; ich połączenia z korpusem wymagają scalenia przed drukiem.' : ''}</p>
      </section>

      <section className="studio-panel studio-inspector" aria-labelledby="dimensions-heading">
        <div className="studio-panel-heading"><span>02</span><h2 id="dimensions-heading">Wymiary i detale</h2></div>
        <label className="studio-select">Bryła<select value={spec.shape} onChange={e => change({ shape: e.target.value as ModelSpec['shape'] })}>{Object.entries(SHAPE_NAMES).map(([key,label]) => <option key={key} value={key}>{label}</option>)}</select></label>
        <div className="studio-unit"><span>Jednostki</span><div role="group" aria-label="Jednostki">{(['mm','cm'] as const).map(u => <button key={u} aria-pressed={unit===u} onClick={() => setUnit(u)}>{u}</button>)}</div></div>
        <NumberField label="Średnica korpusu" value={spec.diameter/scale} min={1/scale} max={500/scale} step={.1/scale} suffix={unit} onChange={v => change({ diameter: v*scale })} />
        <NumberField label="Wysokość" value={spec.height/scale} min={2/scale} max={1000/scale} step={.1/scale} suffix={unit} onChange={v => change({ height: v*scale })} />
        <p className="studio-helper">Okrągły korpus: X = Z. Gabaryty z lotkami widać pod modelem.</p>
        {spec.shape === 'rocket' && <NumberField label="Kąt wierzchołkowy nosa" value={spec.noseAngle} min={20} max={120} suffix="°" onChange={v => change({ noseAngle: v })} />}
        <label className="studio-select">Dokładność okręgu<select value={spec.segments} onChange={e => change({ segments: Number(e.target.value) })}><option value={64}>64 segmenty</option><option value={128}>128 · wysoka</option><option value={256}>256 · bardzo wysoka</option></select></label>
        <small className="studio-helper">Odchyłka cięciwy korpusu ≤ {model.qa.circularChordErrorMm.toFixed(5)} mm. Siatka przybliża idealny okrąg.</small>
        {spec.shape === 'rocket' && <div className="studio-details"><label><input type="checkbox" checked={spec.windows} onChange={e => change({ windows: e.target.checked })} />Okno na teksturze</label><label><input type="checkbox" checked={spec.fins} onChange={e => change({ fins: e.target.checked })} />Cztery lotki</label></div>}
        <h3 className="studio-material-title">Materiał i tekstura</h3>
        <label className="studio-select">Wygląd powierzchni<select value={spec.material} onChange={e => change({ material: e.target.value as ModelSpec['material'] })}><option value="metal">Metal · panele</option><option value="ceramic">Ceramika · gładka</option><option value="carbon">Karbon · splot</option></select></label>
        <div className="studio-colors"><label>Kolor korpusu<input type="color" value={spec.color} onChange={e => change({ color: e.target.value })} /></label><label>Akcent<input type="color" value={spec.accent} onChange={e => change({ accent: e.target.value })} /></label></div>
        <div className="studio-texture"><img alt="Wygenerowana tekstura UV aktualnego modelu" src={`data:image/png;base64,${base64(model.texture)}`} /><div><b>Tekstura UV</b><small>128 × 128 px · PNG</small><button onClick={() => download('png')}>Pobierz teksturę ↓</button></div></div>
        <button className="studio-reset" onClick={() => updateStudio({ ...INITIAL_SPEC }, 'Przywrócono rakietę Ø 10 × 50 mm.')}>Przywróć model startowy</button>
      </section>
    </div>
    <footer className="studio-footer"><span>FROGE MPC 2 · Modelowanie jest pierwszym etapem naszego sklepu.</span><Link to="/contest">Fundament konkursowy →</Link><Link to="/shop-lab">Laboratorium ofert →</Link></footer>
  </div>
}
