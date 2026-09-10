import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { RemoteGenerator } from '../blender/RemoteGenerator'
import { blenderRequest } from '../blender/client'
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.useRealTimers() })

it('recovers a texture failure only after the worker confirms the patch and submits a saved plan without photos or AI', async () => {
  const failed = { id: '12345678-1234-4234-8234-123456789abc', prompt: 'Dziewczyna z mojego zdjęcia', state: 'failed', detail: 'ValueError: Use at most 8 materials and 8 images.', hasModel: false, referencePhotos: [{ name: 'front.jpg', view: 'front', url: '/private-photo' }] }
  let installed = false
  let accepted = failed
  const fetcher = vi.fn(async (url, init) => {
    if (String(url).endsWith('/connection')) return Response.json({ connected: true, ready: false, connectorVersion: installed ? 15 : 14, portraitRevision: installed ? 1 : 0, provider: 'ollama', sceneReplay: installed, rendererRevision: installed ? 2 : 1 })
    if (init?.method === 'POST') { accepted = { ...failed, id: JSON.parse(init.body).id, state: 'queued', detail: 'Wykonuję zapisany plan' }; return Response.json({ job: accepted }) }
    return Response.json(String(url).endsWith('/jobs') ? { jobs: [failed] } : { job: accepted })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt="Inny opis w formularzu" onStart={() => 1} onResult={vi.fn()}/>)
  expect(await screen.findByRole('link', { name: 'Pobierz poprawkę tekstur' })).toHaveAttribute('href', '/downloads/froge-napraw-tekstury.py')
  expect(screen.queryByRole('button', { name: 'Ponów z tymi zdjęciami' })).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Wykonaj zapisany plan bez AI' })).not.toBeInTheDocument()
  expect(fetcher.mock.calls.filter(([, init]) => init?.method === 'POST')).toHaveLength(0)
  installed = true
  fireEvent.click(screen.getByRole('button', { name: /Sprawdź (połączenie z Oracle|serwer po aktualizacji)/ }))
  const replay = await screen.findByRole('button', { name: 'Wykonaj zapisany plan bez AI' })
  expect(replay).toBeEnabled()
  fireEvent.click(replay); fireEvent.click(replay)
  await waitFor(() => expect(fetcher.mock.calls.filter(([, init]) => init?.method === 'POST')).toHaveLength(1))
  const body = JSON.parse(fetcher.mock.calls.find(([, init]) => init?.method === 'POST')![1].body)
  expect(body).toEqual({ id: expect.any(String), prompt: failed.prompt, sourceJobId: failed.id })
})

it('explains the live legacy-worker blocker and confirms an actual upgrade without submitting a job', async () => {
  let finishCheck: (response: Response) => void = () => {}
  let checks = 0
  const fetcher = vi.fn((url, _init) => {
    if (!String(url).endsWith('/connection')) return Promise.resolve(Response.json({ jobs: [] }))
    if (++checks === 1) return Promise.resolve(Response.json({ connected: true, ready: true, connectorVersion: 1, provider: 'ollama', detail: 'AI i Blender sa gotowe.' }))
    return new Promise<Response>(resolve => { finishCheck = resolve })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt="Model ze zdjęcia" onStart={() => 1} onResult={vi.fn()}/>)
  await screen.findByText('Generator na Oracle: v1 · zdjęcia: niedostępne')
  expect(screen.queryByText('AI i Blender sa gotowe.')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Generuj model 3D' })).toBeDisabled()
  expect(screen.getByText(/^Generowanie nie zostało uruchomione\./)).toHaveTextContent('Samo przesłanie ZIP-a nie uruchamia aktualizacji.')
  fireEvent.click(screen.getByRole('button', { name: 'Sprawdź serwer po aktualizacji' }))
  expect(screen.getByRole('button', { name: 'Sprawdzam połączenie…' })).toBeDisabled()
  finishCheck(Response.json({ connected: true, ready: true, connectorVersion: 14, provider: 'openai', photoInput: true }))
  await screen.findByText('Generator na Oracle: v14 · zdjęcia: obsługiwane')
  expect(screen.getByRole('button', { name: 'Generuj model 3D' })).toBeEnabled()
  expect(fetcher.mock.calls.some(([, init]) => init?.method === 'POST')).toBe(false)
})

it('releases the Generate button after a preparation exception and shows sending until the server accepts', async () => {
  let finishSubmission: (response: Response) => void = () => {}
  const start = vi.fn().mockImplementationOnce(() => { throw new Error('Nie udało się przygotować podglądu.') }).mockReturnValue(2)
  const fetcher = vi.fn((url, init) => {
    if (String(url).endsWith('/connection')) return Promise.resolve(Response.json({ connected: true, ready: true, connectorVersion: 14 }))
    if (init?.method === 'POST') return new Promise<Response>(resolve => { finishSubmission = resolve })
    return Promise.resolve(Response.json({ jobs: [] }))
  })
  vi.stubGlobal('fetch', fetcher)
  const view = render(<RemoteGenerator prompt="Dąb" onStart={start} onResult={vi.fn()}/>)
  await waitFor(() => expect(screen.getByRole('button', { name: 'Generuj model 3D' })).toBeEnabled())
  fireEvent.click(screen.getByRole('button', { name: 'Generuj model 3D' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Nie udało się przygotować podglądu.')
  expect(screen.getByRole('button', { name: 'Generuj model 3D' })).toBeEnabled()
  expect(fetcher.mock.calls.some(([, init]) => init?.method === 'POST')).toBe(false)
  fireEvent.click(screen.getByRole('button', { name: 'Generuj model 3D' }))
  expect(screen.getByRole('button', { name: 'Wysyłam zlecenie…' })).toBeDisabled()
  expect(screen.queryByRole('button', { name: 'Generowanie w toku…' })).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Wysyłam zlecenie…' }))
  expect(fetcher.mock.calls.filter(([, init]) => init?.method === 'POST')).toHaveLength(1)
  finishSubmission(Response.json({ error: 'Serwer chwilowo niedostępny.' }, { status: 502 }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Serwer chwilowo niedostępny.')
  expect(screen.getByRole('button', { name: 'Generuj model 3D' })).toBeEnabled()
  view.unmount()
})

it('keeps a completed model in history without filling the new prompt or submitting a job',async()=>{
 const job={id:'12345678-1234-4234-8234-123456789abc',prompt:'Wokalistka Nova',state:'succeeded',detail:'Gotowy w 29.4 s',hasModel:true}
 const restore=vi.fn(),reuse=vi.fn(),onResult=vi.fn(async()=>true)
 const remote=vi.fn(async(url)=>String(url).endsWith('/connection')?Response.json({connected:true,ready:true,connectorVersion:13}):String(url).endsWith('/jobs')?Response.json({jobs:[job]}):String(url).endsWith('/model')?new Response(new Uint8Array([1,2,3]),{headers:{'Content-Type':'model/gltf-binary'}}):Response.json({job}))
 vi.stubGlobal('fetch',remote)
 render(<RemoteGenerator prompt="" onStart={()=>1} onResult={onResult} onRestorePrompt={restore} onReusePrompt={reuse}/>)
 await screen.findByText('Zapisany model w podglądzie')
 expect(restore).not.toHaveBeenCalled()
 expect(screen.getByText(job.prompt).closest('details')).not.toHaveAttribute('open')
 expect(screen.getByText('Wpisz opis albo dodaj zdjęcia.')).toBeInTheDocument()
 fireEvent.click(screen.getByRole('button',{name:'Edytuj opis tego modelu'}))
 expect(reuse).toHaveBeenCalledWith(job.prompt)
 expect(remote.mock.calls.every(call=>call.length===1||!((call as unknown[])[1] as RequestInit)?.method)).toBe(true)
})

it('does not replace an explicitly selected example with a late history response',async()=>{
 const job={id:'12345678-1234-4234-8234-123456789abc',prompt:'Poprzednia Nova',state:'succeeded',detail:'Gotowy',hasModel:true}
 let finishHistory:(response:Response)=>void=()=>{},explicit=false
 const start=vi.fn(()=>1),result=vi.fn(async()=>true),restore=vi.fn()
 const remote=vi.fn((url)=>String(url).endsWith('/connection')?Promise.resolve(Response.json({connected:true,ready:true,connectorVersion:13})):new Promise<Response>(resolve=>{finishHistory=resolve}))
 vi.stubGlobal('fetch',remote)
 render(<RemoteGenerator prompt="" onStart={start} onResult={result} canAutoRestore={()=>!explicit} onRestorePrompt={restore}/>)
 await screen.findByText('Lokalny Qwen + Blender')
 explicit=true;finishHistory(Response.json({jobs:[job]}))
 await screen.findByText('Poprzednie modele')
 expect(start).not.toHaveBeenCalled();expect(result).not.toHaveBeenCalled();expect(restore).not.toHaveBeenCalled()
 expect(remote.mock.calls.some(([url])=>String(url).endsWith('/model'))).toBe(false)
})

it('recovers the same job after a lost mobile connection without starting another generation', async () => {
  const job = { id: '12345678-1234-4234-8234-123456789abc', prompt: 'Dąb z 20 lampkami', state: 'generating', detail: 'AI projektuje scenę: 205 znaków. Ostatnie dane 0 s temu.', hasModel: false }
  let reachable = false
  const onResult = vi.fn(async () => true)
  const fetcher = vi.fn(async (url, _init) => {
    const path = String(url)
    if (path.endsWith('/connection')) return Response.json({ connected: true, ready: true, provider: 'ollama', connectorVersion: 11 })
    if (path.endsWith('/jobs')) return Response.json({ jobs: [job] })
    if (!reachable) throw new TypeError('Failed to fetch')
    if (path.endsWith('/model')) return new Response(new Uint8Array([1, 2, 3]), { headers: { 'Content-Type': 'model/gltf-binary' } })
    return Response.json({ job: { ...job, state: 'succeeded', detail: 'Model gotowy', hasModel: true } })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt={job.prompt} onStart={() => 8} onResult={onResult}/>)
  await screen.findByText('Postęp chwilowo niedostępny')
  expect(screen.getByText(job.detail).closest('details')).not.toHaveAttribute('open')
  expect(screen.queryByText('Failed to fetch')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Podłącz Astrę' })).toBeEnabled()
  expect(screen.getByRole('button', { name: 'Generowanie w toku…' })).toBeDisabled()
  reachable = true
  fireEvent(window, new Event('online'))
  await screen.findByText('Nowy model w podglądzie')
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  expect(onResult).toHaveBeenCalledExactlyOnceWith(expect.anything(), expect.objectContaining({ id: job.id, state: 'succeeded' }), 8)
  expect(fetcher.mock.calls.every(([, init]) => !init?.method || init.method === 'GET')).toBe(true)
})

it('ends a stalled request so that status recovery can continue', async () => {
  vi.useFakeTimers()
  vi.stubGlobal('fetch', vi.fn((_url, options) => new Promise((_resolve, reject) => {
    options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
  })))
  const request = blenderRequest('connection')
  const rejected = expect(request).rejects.toMatchObject({ retryable: true, message: 'Nie otrzymałem odpowiedzi na czas. Sprawdź połączenie z internetem.' })
  await vi.advanceTimersByTimeAsync(60000)
  await rejected
})

it('asks for sign-in after an expired session instead of continually treating it as generation progress', async () => {
  const job = { id: '12345678-1234-4234-8234-123456789abc', prompt: 'Dąb', state: 'generating', detail: '', hasModel: false }
  vi.stubGlobal('fetch', vi.fn(async url => Response.json(String(url).endsWith('/connection') ? { connected: true, ready: true, connectorVersion: 11 } : String(url).endsWith('/jobs') ? { jobs: [job] } : { error: 'Authentication required' }, { status: String(url).endsWith(job.id) ? 401 : 200 })))
  render(<RemoteGenerator prompt="Dąb" onStart={() => 1} onResult={vi.fn()}/>)
  await screen.findByRole('button', { name: 'Odśwież i zaloguj się' })
  expect(screen.queryByText('Ponawiam odczyt tego samego zlecenia.')).not.toBeInTheDocument()
})

it.each([5, 6])('requires the geometry update on worker v%i', async version => {
  const job = { id: '12345678-1234-4234-8234-123456789abc', prompt: 'Dąb', state: 'failed', detail: '/work/generate.py cannot unpack non-iterable Object object', hasModel: false }
  vi.stubGlobal('fetch', vi.fn(async url => Response.json(String(url).endsWith('/connection') ? { connected: true, ready: true, connectorVersion: version } : String(url).endsWith('/jobs') ? { jobs: [job] } : { job })))
  render(<RemoteGenerator prompt="Dąb" onStart={() => 1} onResult={vi.fn()}/>)
  await screen.findByText('Włącz generator postaci · v20')
  await screen.findByText('Nie udało się wygenerować modelu')
  expect(screen.queryByRole('button', { name: 'Wykonaj zapisany skrypt' })).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Generuj model 3D' })).toBeDisabled()
})

it('offers saved-script execution without requiring ready AI or submitting a new description', async () => {
  const original = { id: '12345678-1234-4234-8234-123456789abc', prompt: 'Dąb z lampkami', state: 'failed', detail: '/work/generate.py generated_type RGBA', hasModel: false }
  const fetcher = vi.fn(async (url, init) => {
    const path = String(url)
    if (path.endsWith('/connection')) return Response.json({ connected: true, ready: false, connectorVersion: 11 })
    if (path.endsWith('/jobs') && init?.method === 'POST') return Response.json({ job: { ...original, ...JSON.parse(init.body), state: 'failed', detail: 'fixture complete' } })
    if (path.endsWith('/jobs')) return Response.json({ jobs: [original] })
    return Response.json({ job: original })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt="" onStart={() => 1} onResult={vi.fn()}/>)
  const button = await screen.findByRole('button', { name: 'Wykonaj zapisany skrypt' })
  expect(button).toBeEnabled()
  expect(screen.getByText('Szczegóły błędu').parentElement).not.toHaveAttribute('open')
  fireEvent.click(button)
  await waitFor(() => expect(fetcher.mock.calls.some(([, init]) => init?.method === 'POST')).toBe(true))
  const sent = fetcher.mock.calls.find(([, init]) => init?.method === 'POST')!
  expect(JSON.parse(sent[1].body)).toMatchObject({ prompt: original.prompt, sourceJobId: original.id })
  expect(JSON.parse(sent[1].body).id).not.toBe(original.id)
})

it('requires the actual paired server before submitting generation', async () => {
  vi.stubGlobal('fetch', vi.fn(async url => Response.json(String(url).endsWith('/connection') ? { connected: false, ready: false } : { jobs: [] })))
  render(<RemoteGenerator prompt="Dąb" onStart={() => 1} onResult={vi.fn()}/>)
  await screen.findByText('Serwer niepołączony')
  expect(screen.getByRole('button', { name: 'Generuj model 3D' })).toBeDisabled()
  fireEvent.click(screen.getByRole('button', { name: 'Połącz serwer Blendera' }))
  expect(screen.getByLabelText('Kod połączenia')).toHaveAttribute('type', 'password')
})

it('does not mistake an unreachable worker for an outdated worker', async () => {
  vi.stubGlobal('fetch', vi.fn(async url => Response.json(String(url).endsWith('/connection') ? { connected: true, ready: false, detail: 'Brak łączności z serwerem.' } : { jobs: [] })))
  render(<RemoteGenerator prompt="Dąb" onStart={() => 1} onResult={vi.fn()}/>)
  await screen.findByText('Brak łączności z serwerem.')
  expect(screen.queryByText('Włącz generator postaci · v20')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Generuj model 3D' })).toBeDisabled()
})

it.each([7, 8, 9, 10, 11].flatMap(version => ['succeeded', 'failed'].map(state => ({ version, state }))))('worker $version uses the real $state response and never selects a sample', async ({ version, state }) => {
  const onResult = vi.fn(async () => true), prompt = 'Duży dąb z korą i liśćmi'
  const job = { id: '12345678-1234-4234-8234-123456789abc', prompt, state: 'queued', detail: '', hasModel: false }
  const fetcher = vi.fn(async (url, init) => {
    const path = String(url)
    if (path.endsWith('/connection')) return Response.json({ connected: true, ready: true, connectorVersion: version })
    if (path.endsWith('/model')) return new Response(new Uint8Array([1, 2, 3]), { headers: { 'Content-Type': 'model/gltf-binary' } })
    if (path.endsWith('/jobs') && init?.method === 'POST') return Response.json({ job })
    if (path.endsWith('/jobs')) return Response.json({ jobs: [] })
    return Response.json({ job: { ...job, state, detail: state === 'failed' ? 'AI nie ukończyło modelu' : 'ready', hasModel: state === 'succeeded' } })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt={prompt} onStart={() => 7} onResult={onResult}/>)
  await screen.findByText('Lokalny Qwen + Blender')
  expect(screen.getByRole('button', { name: 'Generuj model 3D' })).toBeEnabled()
  if (version < 14) expect(screen.getByText('Pełna aktualizacja generatora · v20')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Generuj model 3D' }))
  await screen.findByText(state === 'succeeded' ? 'Nowy model w podglądzie' : 'Nie udało się wygenerować modelu')
  const submitted = fetcher.mock.calls.find(([, init]) => init?.method === 'POST')!
  expect(JSON.parse(submitted[1].body).prompt).toBe(prompt)
  if (state === 'succeeded') await waitFor(() => expect(onResult).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({ state }), 7))
  else expect(onResult).not.toHaveBeenCalled()
  expect(fetcher.mock.calls.every(([url]) => !String(url).includes('/models/'))).toBe(true)
})

it('retries the saved description after refresh even when the input is empty', async () => {
  const original = { id: '12345678-1234-4234-8234-123456789abc', prompt: 'Duży dąb z korą i liśćmi', state: 'failed', detail: 'timed out', hasModel: false }
  const fetcher = vi.fn(async (url, init) => {
    const path = String(url)
    if (path.endsWith('/connection')) return Response.json({ connected: true, ready: true, connectorVersion: 11 })
    if (path.endsWith('/jobs') && init?.method === 'POST') return Response.json({ job: { ...JSON.parse(init.body), state: 'queued', detail: 'Opis przyjety.', hasModel: false } })
    if (path.endsWith('/jobs')) return Response.json({ jobs: [original] })
    return Response.json({ job: original })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt="" onStart={() => 1} onResult={vi.fn()}/>)
  const retry = await screen.findByRole('button', { name: 'Ponów ten opis' })
  expect(screen.getByText('AI nie odpowiedziało w limicie czasu. Model nie został zapisany.')).toBeInTheDocument()
  fireEvent.click(retry)
  await waitFor(() => expect(fetcher.mock.calls.some(([, init]) => init?.method === 'POST')).toBe(true))
  const [, request] = fetcher.mock.calls.find(([, init]) => init?.method === 'POST')!
  expect(JSON.parse(request.body).prompt).toBe(original.prompt)
  expect(JSON.parse(request.body).id).not.toBe(original.id)
})

it('configures Astra through the owner API and clears the password field after saving', async () => {
  let provider = 'ollama'
  const apiKey = 'sk-fixture-' + 'a'.repeat(30)
  const fetcher = vi.fn(async (url, _init) => {
    const path = String(url)
    if (path.endsWith('/ai')) { provider = 'openai'; return Response.json({ saved: true }) }
    if (path.endsWith('/connection')) return Response.json({ connected: true, ready: true, provider, connectorVersion: 11, model: provider === 'openai' ? 'gpt-6-astra' : 'qwen2.5-coder:7b' })
    return Response.json({ jobs: [] })
  })
  vi.stubGlobal('fetch', fetcher)
  render(<RemoteGenerator prompt="Dąb z lampkami" onStart={() => 1} onResult={vi.fn()}/>)
  await screen.findByText('Lokalny Qwen + Blender')
  fireEvent.click(screen.getByRole('button', { name: 'Ustawienia serwera' }))
  const input = screen.getByLabelText('Klucz API OpenAI')
  expect(input).toHaveAttribute('type', 'password')
  fireEvent.change(input, { target: { value: apiKey } })
  fireEvent.click(screen.getByRole('button', { name: 'Podłącz OpenAI' }))
  await screen.findByText('OpenAI + Blender gotowe')
  expect(input).toHaveValue('')
  const saved = fetcher.mock.calls.find(([url]) => String(url).endsWith('/ai'))!
  expect(JSON.parse(saved[1].body)).toEqual({ provider: 'openai', apiKey })
  expect(localStorage.length).toBe(0)
})

it('recovers a saved job when POST acknowledgement fails without posting a second job',async()=>{
 let submitted=''
 const post=vi.fn()
 vi.stubGlobal('fetch',vi.fn(async(url,init)=>{
  const path=String(url)
  if(path.endsWith('/connection'))return Response.json({connected:true,ready:true,connectorVersion:16,portraitRevision:1,provider:'openai',photoInput:true})
  if(init?.method==='POST'){
   post();submitted=JSON.parse(init.body).id
   return Response.json({error:'Temporary storage failure'},{status:503})
  }
  if(path.endsWith('/jobs'))return Response.json({jobs:[]})
  return Response.json({job:{id:submitted,prompt:'Dąb',state:'failed',detail:'Odzyskane zlecenie',hasModel:false}})
 }))
 render(<RemoteGenerator prompt="Dąb" onStart={()=>1} onResult={async()=>true}/>)
 await screen.findByText('OpenAI + Blender gotowe')
 fireEvent.click(screen.getByRole('button',{name:'Generuj model 3D'}))
 await screen.findByText('Odzyskane zlecenie')
 expect(post).toHaveBeenCalledTimes(1)
})
