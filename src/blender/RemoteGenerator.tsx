import { useEffect, useRef, useState } from 'react'
import { blenderRequest, finished, generatedModel, type BlenderConnection, type GenerationJob } from './client'
import './generator.css'
import { OpenAISettings } from './OpenAISettings'

export const oracleInstallCommand = `scp -o IdentitiesOnly=yes -i "$HOME/ssh-key-2026-09-06.key" "$HOME/froge-oracle-connector.zip" opc@141.148.242.30:/home/opc/froge-oracle-connector.zip &&
ssh -T -o IdentitiesOnly=yes -o ServerAliveInterval=30 -i "$HOME/ssh-key-2026-09-06.key" opc@141.148.242.30 'mkdir -p "$HOME/froge-connector" && python3 -m zipfile -e "$HOME/froge-oracle-connector.zip" "$HOME/froge-connector" && bash "$HOME/froge-connector/install.sh"'`

type Props = { prompt: string; onStart: () => number; onResult: (bytes: ArrayBuffer, job: GenerationJob, revision: number) => Promise<boolean> }
export function RemoteGenerator({ prompt, onStart, onResult }: Props) {
  const [connection, setConnection] = useState<BlenderConnection | null>(null)
  const [endpoint, setEndpoint] = useState(''), [code, setCode] = useState('')
  const [connecting, setConnecting] = useState(false), [submitting, setSubmitting] = useState(false)
  const [setup, setSetup] = useState(false), [error, setError] = useState(''), [copyNote, setCopyNote] = useState('')
  const [active, setActive] = useState<GenerationJob | null>(null), [recent, setRecent] = useState<GenerationJob[]>([])
  const [displayed, setDisplayed] = useState(false)
  const callbacks = useRef({ onStart, onResult }); callbacks.current = { onStart, onResult }
  const revision = useRef(0), serial = useRef(0), loaded = useRef(''), mounted = useRef(true)
  const busy = submitting || (!!active && !finished(active))

  async function refreshConnection() {
    try {
      const result = await blenderRequest<BlenderConnection>('connection')
      if (mounted.current) setConnection(result)
    } catch (e) { if (mounted.current) setError((e as Error).message) }
  }
  function selectJob(job: GenerationJob) {
    serial.current++
    revision.current = callbacks.current.onStart()
    loaded.current = ''
    setDisplayed(false); setError(''); setActive(job)
  }
  useEffect(() => {
    mounted.current = true
    void refreshConnection()
    void blenderRequest<{ jobs: GenerationJob[] }>('jobs').then(({ jobs }) => {
      if (!mounted.current) return
      setRecent(jobs)
      if (serial.current === 0 && jobs.length) selectJob(jobs[0])
    }).catch(e => { if (mounted.current) setError(e.message) })
    const timer = window.setInterval(() => void refreshConnection(), 20000)
    return () => { mounted.current = false; window.clearInterval(timer) }
  }, [])
  useEffect(() => {
    if (!active) return
    let stopped = false, timer: number | undefined
    const jobId = active.id, visualRevision = revision.current
    async function poll() {
      try {
        const { job } = await blenderRequest<{ job: GenerationJob }>('jobs/' + jobId)
        if (stopped) return
        setActive(job)
        setRecent(items => [job, ...items.filter(item => item.id !== job.id)].slice(0, 10))
        setError('')
        if (job.state === 'succeeded' && loaded.current !== jobId) {
          const bytes = await generatedModel(jobId)
          if (stopped) return
          const shown = await callbacks.current.onResult(bytes, job, visualRevision)
          if (stopped) return
          loaded.current = jobId; setDisplayed(shown)
        }
        if (!finished(job)) timer = window.setTimeout(() => void poll(), 5000)
      } catch (e) {
        if (stopped) return
        setError((e as Error).message)
        timer = window.setTimeout(() => void poll(), 10000)
      }
    }
    void poll()
    return () => { stopped = true; if (timer) window.clearTimeout(timer) }
  }, [active?.id])

  async function connect() {
    setConnecting(true); setError('')
    try {
      await blenderRequest('connection', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ endpoint: endpoint.trim(), code: code.trim() }) })
      setCode(''); setSetup(false)
      await refreshConnection()
    } catch (e) { setError((e as Error).message) } finally { setConnecting(false) }
  }
  async function generate(requestedPrompt = prompt) {
    if (busy || !connection?.ready || !requestedPrompt.trim()) return
    setSubmitting(true); setError('')
    const input = { id: crypto.randomUUID(), prompt: requestedPrompt.trim() }
    const requestSerial = ++serial.current
    const nextRevision = callbacks.current.onStart()
    try {
      const { job } = await blenderRequest<{ job: GenerationJob }>('jobs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(input) })
      if (!mounted.current || serial.current !== requestSerial) return
      revision.current = nextRevision; loaded.current = ''
      setDisplayed(false); setActive(job)
      setRecent(items => [job, ...items].slice(0, 10))
    } catch (e) { if (mounted.current) setError((e as Error).message) } finally { if (mounted.current) setSubmitting(false) }
  }
  async function cancel() {
    if (!active || finished(active)) return
    try {
      await blenderRequest('jobs/' + active.id + '/cancel', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
      setActive({ ...active, state: 'cancelled', detail: 'Zlecenie anulowane.' })
    } catch (e) { setError((e as Error).message) }
  }
  async function openModel(job: GenerationJob) {
    try {
      const nextRevision = callbacks.current.onStart()
      const bytes = await generatedModel(job.id)
      setDisplayed(await callbacks.current.onResult(bytes, job, nextRevision))
    } catch (e) { setError((e as Error).message) }
  }
  return <div className="remote-generator">
    <div className="blender-connection" role="status">
      <strong>{connection === null ? 'Sprawdzam serwer…' : connection.ready ? connection.provider === 'openai' ? 'OpenAI + Blender gotowe' : 'AI + Blender gotowe' : connection.connected ? 'Serwer nie jest jeszcze gotowy' : 'Serwer niepołączony'}</strong>
      <p>{connection?.detail || 'Odczytuję zapisane połączenie.'}</p>
      {connection?.model && <small>Model AI: {connection.model}</small>}
      <button onClick={() => setSetup(value => !value)} aria-expanded={setup}>{setup ? 'Zamknij ustawienia' : connection?.connected ? 'Ustawienia serwera' : 'Połącz serwer Blendera'}</button>
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
    <button className="studio-primary" disabled={busy || !connection?.ready || !prompt.trim()} onClick={() => void generate()}>{busy ? 'Generowanie w toku…' : 'Generuj model 3D'}</button>
    <p className="studio-helper">{connection?.provider === 'openai' ? 'OpenAI Astra tworzy instrukcje, a Blender buduje geometrię i materiały. Po zakończeniu zobaczysz zmierzony czas obu etapów.' : 'Instrukcje tworzy lokalny Qwen na Oracle. Możesz podłączyć OpenAI w ustawieniach serwera. Blender zapisuje gotowy model z materiałami.'}</p>
    {active && <div className={'generation-job state-' + active.state} role="status">
      <strong>{active.state === 'succeeded' ? displayed ? 'Nowy model w podglądzie' : 'Model gotowy' : active.state === 'failed' ? 'Nie udało się wygenerować modelu' : active.state === 'cancelled' ? 'Zlecenie anulowane' : 'Pracuję nad modelem'}</strong>
      <p className="generation-prompt">{active.prompt}</p><p>{active.detail === 'timed out' ? 'AI nie odpowiedziało w limicie czasu. Model nie został zapisany.' : active.detail}</p>
      {['failed', 'cancelled'].includes(active.state) && <button disabled={busy || !connection?.ready} onClick={() => void generate(active.prompt)}>Ponów ten opis</button>}
      {!finished(active) && <button onClick={() => void cancel()}>Anuluj zlecenie</button>}
      {active.state === 'succeeded' && !displayed && <button onClick={() => void openModel(active)}>Wczytaj wynik do podglądu</button>}
    </div>}
    {error && <p className="studio-error" role="alert">{error}</p>}
    {recent.filter(job => job.hasModel && job.id !== active?.id).length > 0 && <details className="generation-history"><summary>Poprzednie modele</summary>{recent.filter(job => job.hasModel && job.id !== active?.id).map(job => <button key={job.id} disabled={busy} onClick={() => selectJob(job)}>{job.prompt.slice(0, 100)}</button>)}</details>}
  </div>
}
