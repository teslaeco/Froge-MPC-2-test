import { useEffect, useRef, useState } from 'react'
import { BlenderRequestError, blenderRequest, finished, generatedModel, type BlenderConnection, type GenerationJob } from './client'
import './generator.css'
import { OpenAISettings, GeometryUpdate } from './OpenAISettings'
import { supportsGeneration, supportsPhotoGeneration, RECOMMENDED_CONNECTOR_VERSION, supportsPortraitQuality, requiresPortraitQuality, PORTRAIT_UPDATE_REASON, supportsCoutureQuality, requiresCoutureQuality, COUTURE_UPDATE_REASON } from './compatibility'
import { PhotoReferences } from './PhotoReferences'
import { DEFAULT_PHOTO_PROMPT, PHOTO_VIEWS, type PhotoInput } from './photoReferences'

export const oracleInstallCommand = `scp -o IdentitiesOnly=yes -i "$HOME/ssh-key-2026-09-06.key" "$HOME/froge-oracle-connector.zip" opc@141.148.242.30:/home/opc/froge-oracle-connector.zip &&
ssh -T -o IdentitiesOnly=yes -o ServerAliveInterval=30 -i "$HOME/ssh-key-2026-09-06.key" opc@141.148.242.30 'mkdir -p "$HOME/froge-connector" && python3 -m zipfile -e "$HOME/froge-oracle-connector.zip" "$HOME/froge-connector" && bash "$HOME/froge-connector/install.sh"'`

type Props = { prompt: string; onStart: () => number; onResult: (bytes: ArrayBuffer, job: GenerationJob, revision: number) => Promise<boolean>; canAutoRestore?: () => boolean; onRestorePrompt?: (prompt:string)=>void; onReusePrompt?: (prompt:string)=>void; onNewModel?: (preservePrompt: boolean) => void }
export function RemoteGenerator({ prompt, onStart, onResult, canAutoRestore, onRestorePrompt, onReusePrompt, onNewModel }: Props) {
  const [connection, setConnection] = useState<BlenderConnection | null>(null)
  const [endpoint, setEndpoint] = useState(''), [code, setCode] = useState('')
  const [connecting, setConnecting] = useState(false), [submitting, setSubmitting] = useState(false)
  const [setup, setSetup] = useState(false), [error, setError] = useState(''), [copyNote, setCopyNote] = useState('')
  const [connectionError, setConnectionError] = useState(''), [jobError, setJobError] = useState<Error | null>(null)
  const [checkingConnection, setCheckingConnection] = useState(true), [checkedAt, setCheckedAt] = useState('')
  const [active, setActive] = useState<GenerationJob | null>(null), [recent, setRecent] = useState<GenerationJob[]>([])
  const [displayed, setDisplayed] = useState(false), [fromHistory, setFromHistory] = useState(false)
  const [photos, setPhotos] = useState<PhotoInput[]>([]), [preparingPhotos, setPreparingPhotos] = useState(false)
  const callbacks = useRef({ onStart, onResult, canAutoRestore, onRestorePrompt, onReusePrompt, onNewModel }); callbacks.current = { onStart, onResult, canAutoRestore, onRestorePrompt, onReusePrompt, onNewModel }
  const revision = useRef(0), serial = useRef(0), loaded = useRef(''), mounted = useRef(true)
  const retryPoll = useRef<() => void>(() => {})
  const connectionRequest = useRef<AbortController | null>(null), connectionSerial = useRef(0), submissionLock = useRef(false)
  // Keep the same identifier after a lost acknowledgement. A second click must
  // resolve the original request, never silently buy another AI generation.
  const pendingSubmission = useRef<{ fingerprint: string; id: string } | null>(null)
  const busy = submitting || (!!active && !finished(active))
  const textureLimitFailure = active?.state === 'failed' && active.detail.includes('Use at most 8 materials and 8 images')
  const currentWorker = supportsGeneration(connection?.connectorVersion)
  const canGenerate = !!connection?.connected && !!connection.ready && currentWorker && !connectionError
  const photosSupported = supportsPhotoGeneration(connection)
  const photoBlockedReason = (connection?.connectorVersion ?? 0) < 14 ? 'Zdjęcie jest wybrane. Generowanie odblokuje aktualizacja Oracle do v20 — pobierz ją poniżej. Samo odświeżenie strony nie aktualizuje serwera.' : 'Wybrane AI nie obsługuje zdjęć. W ustawieniach serwera wybierz OpenAI; lokalny Qwen obsługuje tylko opis.'
  const coutureBlocked=requiresCoutureQuality(prompt) && !supportsCoutureQuality(connection)
  const longPromptBlocked=prompt.length>2000 && connection?.promptMaxLength!==5000
  const referenceQualityBlocked = photos.some(p => p.textureMaxSize) && connection?.referenceQualityRevision !== 1
  const portraitBlocked=referenceQualityBlocked || (requiresPortraitQuality(prompt,photos.length) && !supportsPortraitQuality(connection)) || coutureBlocked || longPromptBlocked
  const updateAvailable = !!connection?.connected && connection.connectorVersion !== undefined && connection.connectorVersion < RECOMMENDED_CONNECTOR_VERSION
  const oldWorkerReason = `Oracle zgłasza generator v${connection?.connectorVersion}. Zainstaluj aktualizację v20 na serwerze. Samo przesłanie ZIP-a nie uruchamia aktualizacji.`
  const connectionDetail = connection?.ready && !currentWorker ? oldWorkerReason : connection?.detail || 'Odczytuję zapisane połączenie.'
  const blockedReason = busy ? '' : preparingPhotos ? 'Przygotowuję zdjęcia…' : connectionError ? connectionError : !connection ? 'Sprawdzam, czy serwer może przyjąć zlecenie…' : !connection.connected ? 'Połącz serwer Blendera w ustawieniach powyżej.' : updateAvailable && !currentWorker ? 'Generowanie nie zostało uruchomione. ' + oldWorkerReason : !connection.ready ? 'Generowanie nie zostało uruchomione. ' + connectionDetail : photos.length && !photosSupported ? photoBlockedReason : portraitBlocked ? (referenceQualityBlocked ? 'Referencje 4K/8K wymagają aktualizacji generatora z obsługą jakości referencji.' : coutureBlocked ? COUTURE_UPDATE_REASON : longPromptBlocked ? 'Opis powyżej 2000 znaków wymaga aktualizacji Oracle do v20.' : PORTRAIT_UPDATE_REASON) : !prompt.trim() && !photos.length ? 'Wpisz opis albo dodaj zdjęcia.' : ''

  async function refreshConnection() {
    const requestSerial = ++connectionSerial.current
    connectionRequest.current?.abort()
    const controller = new AbortController()
    connectionRequest.current = controller
    setCheckingConnection(true)
    try {
      const result = await blenderRequest<BlenderConnection>('connection', { signal: controller.signal })
      if (mounted.current && requestSerial === connectionSerial.current) {
        setConnection(result)
        setConnectionError('')
        setCheckedAt(new Date().toLocaleTimeString('pl-PL'))
      }
    } catch (e) { if (mounted.current && requestSerial === connectionSerial.current) setConnectionError((e as Error).message) }
    finally {
      if (mounted.current && requestSerial === connectionSerial.current) {
        connectionRequest.current = null
        setCheckingConnection(false)
      }
    }
  }
  function selectJob(job: GenerationJob) {
    serial.current++
    revision.current = callbacks.current.onStart()
    loaded.current = ''
    setDisplayed(false); setFromHistory(job.state === 'succeeded'); setError(''); setJobError(null); setActive(job)
  }
  function newModel(preservePrompt = false) {
    if (busy) return
    serial.current++
    loaded.current = ''
    setActive(null); setDisplayed(false); setFromHistory(false); setError(''); setJobError(null)
    if (!preservePrompt) setPhotos([])
    callbacks.current.onNewModel?.(preservePrompt)
  }
  function changePhotos(next: PhotoInput[]) {
    if (!photos.length && next.length) newModel(true)
    setPhotos(next)
  }
  useEffect(() => {
    mounted.current = true
    void refreshConnection()
    void blenderRequest<{ jobs: GenerationJob[] }>('jobs').then(({ jobs }) => {
      if (!mounted.current) return
      setRecent(jobs)
      if (serial.current === 0 && jobs.length && (callbacks.current.canAutoRestore?.() ?? true)) {
        if (!finished(jobs[0])) callbacks.current.onRestorePrompt?.(jobs[0].prompt)
        selectJob(jobs[0])
      }
    }).catch(e => { if (mounted.current) setError(e.message) })
    const timer = window.setInterval(() => { if (!connectionRequest.current) void refreshConnection() }, 20000)
    return () => { mounted.current = false; connectionSerial.current++; connectionRequest.current?.abort(); connectionRequest.current = null; window.clearInterval(timer) }
  }, [])
  useEffect(() => {
    if (!active) return
    let stopped = false, inFlight = false, timer: number | undefined
    const controller = new AbortController()
    const jobId = active.id, visualRevision = revision.current
    async function poll() {
      if (stopped || inFlight) return
      if (timer) window.clearTimeout(timer)
      inFlight = true
      let nextPoll: number | undefined
      try {
        const { job } = await blenderRequest<{ job: GenerationJob }>('jobs/' + jobId, { signal: controller.signal })
        if (stopped) return
        setActive(job)
        setRecent(items => [job, ...items.filter(item => item.id !== job.id)].slice(0, 10))
        if (job.state === 'succeeded' && loaded.current !== jobId) {
          const bytes = await generatedModel(jobId, { signal: controller.signal })
          if (stopped) return
          const shown = await callbacks.current.onResult(bytes, job, visualRevision)
          if (stopped) return
          loaded.current = jobId; setDisplayed(shown)
        }
        setJobError(null)
        if (!finished(job)) nextPoll = 5000
      } catch (e) {
        if (stopped) return
        setJobError(e as Error)
        if (e instanceof BlenderRequestError && e.retryable) nextPoll = 10000
      } finally {
        inFlight = false
        if (!stopped && nextPoll) timer = window.setTimeout(() => void poll(), nextPoll)
      }
    }
    const retry = () => void poll()
    const visible = () => { if (document.visibilityState === 'visible') retry() }
    retryPoll.current = retry
    window.addEventListener('online', retry)
    document.addEventListener('visibilitychange', visible)
    void poll()
    return () => {
      stopped = true; controller.abort()
      if (timer) window.clearTimeout(timer)
      window.removeEventListener('online', retry)
      document.removeEventListener('visibilitychange', visible)
      retryPoll.current = () => {}
    }
  }, [active?.id])

  async function connect() {
    setConnecting(true); setError('')
    try {
      await blenderRequest('connection', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ endpoint: endpoint.trim(), code: code.trim() }) })
      setCode(''); setSetup(false)
      await refreshConnection()
    } catch (e) { setError((e as Error).message) } finally { setConnecting(false) }
  }
  async function generate(requestedPrompt = prompt, sourceJobId?: string, referenceJobId?: string, useDraftPhotos = true) {
    const attached = useDraftPhotos && !sourceJobId && !referenceJobId ? photos : []
    const withPhotos = !!referenceJobId || attached.length > 0
    const description = requestedPrompt.trim() || (withPhotos ? DEFAULT_PHOTO_PROMPT : '')
    if (submissionLock.current || busy || preparingPhotos || !currentWorker || !(sourceJobId ? connection?.connected : canGenerate) || !description) return
    if (attached.some(p => p.textureMaxSize) && connection?.referenceQualityRevision !== 1) { setError('Zaktualizuj generator, aby zachować jakość referencji 4K/8K.'); return }
    if (withPhotos && !photosSupported) { setError(photoBlockedReason); return }
    if (requiresPortraitQuality(description, withPhotos ? 1 : 0) && !supportsPortraitQuality(connection)) { setError(PORTRAIT_UPDATE_REASON); return }
    if (requiresCoutureQuality(description) && !supportsCoutureQuality(connection)) { setError(COUTURE_UPDATE_REASON); return }
    if (description.length>2000 && connection?.promptMaxLength!==5000) { setError('Opis powyżej 2000 znaków wymaga aktualizacji Oracle do v20.'); return }
    submissionLock.current = true
    setSubmitting(true); setError('')
    try {
      const payload = { prompt: description, ...(sourceJobId ? { sourceJobId } : {}), ...(referenceJobId ? { referenceJobId } : {}), ...(attached.length ? { photos: attached } : {}) }
      const fingerprint = JSON.stringify(payload)
      const id = pendingSubmission.current?.fingerprint === fingerprint ? pendingSubmission.current.id : crypto.randomUUID()
      pendingSubmission.current = { fingerprint, id }
      const input = { id, ...payload }
      const requestSerial = ++serial.current
      const nextRevision = callbacks.current.onStart()
      let result: { job: GenerationJob }
      try {
        result = await blenderRequest<{ job: GenerationJob }>('jobs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(input) })
      } catch (failure) {
        if (!(failure instanceof BlenderRequestError) || !failure.retryable) { pendingSubmission.current = null; throw failure }
        // The server may have saved/accepted the job before the response failed.
        try {
          result = await blenderRequest<{ job: GenerationJob }>('jobs/' + id)
          if (!result?.job || result.job.id !== id) throw failure
        }
        catch { throw failure }
      }
      const { job } = result
      pendingSubmission.current = null
      if (!mounted.current || serial.current !== requestSerial) return
      revision.current = nextRevision; loaded.current = ''
      setDisplayed(false); setFromHistory(false); setJobError(null); setActive(job)
      setRecent(items => [job, ...items].slice(0, 10))
    } catch (e) { if (mounted.current) setError(e instanceof Error ? e.message : 'Nie udało się wysłać zlecenia. Spróbuj ponownie.') } finally { submissionLock.current = false; if (mounted.current) setSubmitting(false) }
  }
  async function cancel() {
    if (!active || finished(active)) return
    try {
      await blenderRequest('jobs/' + active.id + '/cancel', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
      setActive({ ...active, state: 'cancelled', detail: 'Zlecenie anulowane.' })
    } catch (e) { setError((e as Error).message) }
  }
  async function openModel(job: GenerationJob) {
    const requestSerial = ++serial.current
    try {
      const nextRevision = callbacks.current.onStart()
      const bytes = await generatedModel(job.id)
      if (!mounted.current || serial.current !== requestSerial) return
      const shown = await callbacks.current.onResult(bytes, job, nextRevision)
      if (mounted.current && serial.current === requestSerial) setDisplayed(shown)
    } catch (e) { setError((e as Error).message) }
  }
  return <div className="remote-generator">
    <button className="new-model-button" disabled={busy || preparingPhotos} onClick={() => newModel()}>Nowy model · wyczyść formularz</button>
    <div className="blender-connection" role="status">
      <strong>{connectionError ? 'Nie udało się sprawdzić połączenia' : connection === null ? 'Sprawdzam serwer…' : connection.ready && !currentWorker ? 'Generator wymaga aktualizacji' : connection.ready ? connection.provider === 'openai' ? 'OpenAI + Blender gotowe' : 'Lokalny Qwen + Blender' : connection.connected ? 'Serwer nie jest jeszcze gotowy' : 'Serwer niepołączony'}</strong>
      <p>{connectionDetail}</p>
      {connection?.connectorVersion !== undefined && <small>Generator na Oracle: v{connection.connectorVersion} · zdjęcia: {photosSupported ? 'obsługiwane' : 'niedostępne'}</small>}
      {connection?.connectorVersion !== undefined && <small>Standard postaci: {supportsCoutureQuality(connection) ? `v${connection.characterStandard ?? connection.connectorVersion} · suknia i wachlarz` : supportsPortraitQuality(connection) ? `v${connection.characterStandard ?? connection.connectorVersion} · anatomia` : 'nieaktywny'}</small>}
      {connection?.model && <small>Model AI: {connection.model}</small>}
      {checkedAt && !connectionError && <small>Ostatnie sprawdzenie: {checkedAt}</small>}
      <button onClick={() => setSetup(value => !value)} aria-expanded={setup}>{setup ? 'Zamknij ustawienia' : connection?.connected ? 'Ustawienia serwera' : 'Połącz serwer Blendera'}</button>
      {connection?.connected && connection.provider !== 'openai' && !setup && <button onClick={() => setSetup(true)}>Podłącz Astrę</button>}
      {connectionError && <p className="studio-error" role="alert">{connectionError}</p>}
    </div>
    {setup && connection?.connected && <OpenAISettings connection={connection} busy={busy} onSaved={refreshConnection}/>}
    {setup && <details className="blender-setup" open={!connection?.connected}>
      <summary>{connection?.connected ? 'Zmień połączenie z Oracle' : 'Połącz Oracle'}</summary>
      <details><summary>Pierwsze połączenie z Oracle</summary>
        <ol><li><a href="/downloads/froge-oracle-connector.zip" download>Pobierz instalator Oracle</a>.</li><li>Prześlij ZIP w Oracle Cloud Shell przez Menu → Upload.</li><li>Wklej poniższe polecenie do Cloud Shell. Łączy się z Twoją obecną maszyną i instaluje lokalne AI oraz program obsługujący zlecenia.</li></ol>
        <pre tabIndex={0}>{oracleInstallCommand}</pre>
        <button onClick={() => { if (!navigator.clipboard) { setCopyNote('Zaznacz polecenie powyżej i skopiuj je ręcznie.'); return } void navigator.clipboard.writeText(oracleInstallCommand).then(() => setCopyNote('Skopiowano polecenie.'), () => setCopyNote('Zaznacz polecenie powyżej i skopiuj je ręcznie.')) }}>Kopiuj polecenie instalacji</button>
        {copyNote && <p role="status">{copyNote}</p>}
        <p>Instalator pobierze około 4,7 GB modelu AI oraz programy pomocnicze. Używa obecnego serwera i nie włącza płatnego API.</p>
      </details>
      <label>Adres HTTPS z instalatora<input type="url" value={endpoint} onChange={e => setEndpoint(e.target.value)} placeholder="https://…trycloudflare.com" autoCapitalize="none" autoCorrect="off" spellCheck={false}/></label>
      <label>Kod połączenia<input type="password" value={code} onChange={e => setCode(e.target.value)} autoComplete="off" autoCapitalize="none" spellCheck={false} maxLength={64}/></label>
      <button disabled={connecting || !endpoint.trim() || !code.trim()} onClick={() => void connect()}>{connecting ? 'Łączę…' : 'Zapisz połączenie'}</button>
      <p>Wklej kod wyświetlony przez instalator. Klucz SSH pozostaje w Oracle Cloud Shell.</p>
      <p>Połączenie korzysta z tunelu testowego. Po jego restarcie adres może się zmienić.</p>
    </details>}
    <PhotoReferences photos={photos} onChange={changePhotos} disabled={busy} onPreparing={setPreparingPhotos}/>
    <button className="studio-primary" aria-describedby="generation-blocked-reason" disabled={busy || preparingPhotos || !canGenerate || (!prompt.trim() && !photos.length) || (photos.length > 0 && !photosSupported) || portraitBlocked} onClick={() => void generate()}>{submitting ? 'Wysyłam zlecenie…' : busy ? 'Generowanie w toku…' : photos.length ? 'Generuj model 3D ze zdjęć' : 'Generuj model 3D'}</button>
    <p id="generation-blocked-reason" className="studio-helper" role="status">{submitting ? 'Czekam na potwierdzenie przyjęcia zlecenia. Generowanie jeszcze nie zostało potwierdzone.' : blockedReason}</p>
    {connection?.connected && (portraitBlocked || updateAvailable) && <GeometryUpdate required={portraitBlocked || !currentWorker}/>}
    {supportsPortraitQuality(connection) && <p className="studio-helper">Standard postaci aktywny: anatomiczna twarz i dłonie, paznokcie oraz kontrola eksportu. Podobieństwo do zdjęcia oceniasz w podglądzie.</p>}
    <button disabled={checkingConnection} aria-busy={checkingConnection} onClick={() => void refreshConnection()}>{checkingConnection ? 'Sprawdzam połączenie…' : updateAvailable ? 'Sprawdź serwer po aktualizacji' : 'Sprawdź połączenie z Oracle'}</button>
    {!prompt.trim() && !photos.length && recent[0] && onReusePrompt && <button onClick={()=>onReusePrompt(recent[0].prompt)}>Przywróć ostatni opis</button>}
    <p className="studio-helper">{connection?.provider === 'openai' ? 'Astra analizuje opis i dołączone zdjęcia, a Blender tworzy geometrię i materiały. Generowanie korzysta z płatnego OpenAI API na Twoim koncie; samo dodanie zdjęć niczego nie uruchamia.' : 'Wybrany jest lokalny Qwen, który może działać wolno na tym serwerze i obsługuje tylko tekst. Przycisk „Podłącz Astrę” pozwala wybrać OpenAI API.'}</p>
    {active && !submitting && <div className={'generation-job state-' + active.state} role="status">
      <strong>{jobError && !finished(active) ? 'Postęp chwilowo niedostępny' : active.state === 'succeeded' ? displayed ? fromHistory ? 'Zapisany model w podglądzie' : 'Nowy model w podglądzie' : 'Model gotowy' : active.state === 'failed' ? 'Nie udało się wygenerować modelu' : active.state === 'cancelled' ? 'Zlecenie anulowane' : 'Pracuję nad modelem'}</strong>
      {finished(active) ? <details className="saved-job-prompt"><summary>Opis tego zlecenia</summary><p className="generation-prompt">{active.prompt}</p></details> : <p className="generation-prompt">{active.prompt}</p>}
      {!!active.referencePhotos?.length && <div className="photo-reference-grid job-photos" aria-label="Zdjęcia tego zlecenia">{active.referencePhotos.map((photo, index) => <a href={photo.url} target="_blank" rel="noreferrer" key={photo.url}><img src={photo.url} alt={`Referencja ${index + 1}: ${photo.name}`} loading="lazy"/><span>{PHOTO_VIEWS[photo.view]}</span></a>)}</div>}
      {jobError && !finished(active) ? <>
        <p>Zlecenie może nadal działać na Oracle. Sprawdzam jego status.</p>
        <details><summary>Ostatni odebrany status</summary><p>{active.detail}</p></details>
      </> : textureLimitFailure ? <>
        <p>Plan modelu został zapisany na Oracle. Eksport zatrzymał się przez błędny limit tekstur.</p>
        {connection?.sceneReplay && (connection.rendererRevision ?? 0) >= 2 ? <>
          <p>Poprawka tekstur jest zainstalowana. Możesz wykonać zapisany plan bez kolejnego zapytania do AI.</p>
          <button disabled={busy || !connection.connected || !!connectionError} onClick={() => void generate(active.prompt, active.id, undefined, false)}>Wykonaj zapisany plan bez AI</button>
        </> : <>
          <p>Pobierz poprawkę, prześlij plik do Cloud Shell i uruchom poniższe polecenie. Następnie sprawdź połączenie z Oracle na tej stronie.</p>
          <a href="/downloads/froge-napraw-tekstury.py" download>Pobierz poprawkę tekstur</a>
          <pre><code>python3 "$HOME/froge-napraw-tekstury.py"</code></pre>
        </>}
        <details><summary>Szczegóły błędu</summary><p>{active.detail}</p></details>
      </> : active.state === 'failed' && active.detail.includes('/work/generate.py') ? <>
        <p>Wygenerowany skrypt zawiera błąd. Model nie został utworzony.</p>
        <details><summary>Szczegóły błędu</summary><p>{active.detail}</p></details>
        {currentWorker && active.detail.includes('RGBA') ? <>
          <p>Możesz wykonać zapisany skrypt z poprawioną funkcją materiałów. Nie wysyłamy wtedy nowego zapytania do AI.</p>
          <button disabled={busy || !connection?.connected} onClick={() => void generate(active.prompt, active.id)}>Wykonaj zapisany skrypt</button>
        </> : <p>Ten skrypt pochodzi ze starego generatora. Utwórz nowy model po aktualizacji, korzystając ze sprawdzanego planu sceny.</p>}
      </> : <p>{active.detail === 'timed out' ? 'AI nie odpowiedziało w limicie czasu. Model nie został zapisany.' : active.detail}</p>}
      {['failed', 'cancelled'].includes(active.state) && !textureLimitFailure && <button disabled={busy || !canGenerate || (!!active.referencePhotos?.length && !photosSupported)} onClick={() => void generate(active.prompt, undefined, active.referencePhotos?.length ? active.id : undefined, false)}>{active.referencePhotos?.length ? 'Ponów z tymi zdjęciami' : 'Ponów ten opis'}</button>}
      {!finished(active) && <button onClick={() => void cancel()}>Anuluj zlecenie</button>}
      {active.state === 'succeeded' && !displayed && <button onClick={() => void openModel(active)}>Wczytaj wynik do podglądu</button>}
      {active.state === 'succeeded' && onReusePrompt && <button onClick={()=>onReusePrompt(active.prompt)}>Edytuj opis tego modelu</button>}
      {jobError && <div className="studio-error" role="alert">
        <p>{jobError.message}</p>
        {jobError instanceof BlenderRequestError && jobError.retryable && <p>Ponawiam odczyt tego samego zlecenia.</p>}
        {jobError instanceof BlenderRequestError && [401, 403].includes(jobError.status)
          ? <button onClick={() => window.location.reload()}>Odśwież i zaloguj się</button>
          : <button onClick={() => retryPoll.current()}>Sprawdź status teraz</button>}
      </div>}
    </div>}
    {error && <p className="studio-error" role="alert">{error}</p>}
    {recent.filter(job => job.hasModel && job.id !== active?.id).length > 0 && <details className="generation-history"><summary>Poprzednie modele</summary>{recent.filter(job => job.hasModel && job.id !== active?.id).map(job => <button key={job.id} disabled={busy} onClick={() => selectJob(job)}>{job.prompt.slice(0, 100)}</button>)}</details>}
  </div>
}
