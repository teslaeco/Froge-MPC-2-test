import { useEffect, useRef, useState } from 'react'

type ResultEvent = { resultIndex: number; results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }> }
type Recognition = { lang: string; continuous: boolean; interimResults: boolean; onresult: ((e: ResultEvent) => void) | null; onerror: ((e: { error: string }) => void) | null; onend: (() => void) | null; onstart: (() => void) | null; start: () => void; abort: () => void }
type SpeechWindow = Window & { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition }
export function useDictation(onText: (text: string) => void) {
  const [listening, setListening] = useState(false), [interim, setInterim] = useState(''), [error, setError] = useState('')
  const recognition = useRef<Recognition | null>(null), callback = useRef(onText)
  useEffect(() => { callback.current = onText }, [onText])
  const w = typeof window === 'undefined' ? undefined : window as SpeechWindow
  const Constructor = w?.SpeechRecognition ?? w?.webkitSpeechRecognition
  useEffect(() => () => { if (recognition.current) { recognition.current.onend = null; recognition.current.onresult = null; recognition.current.onerror = null; recognition.current.onstart = null; recognition.current.abort() } }, [])
  function stop() { recognition.current?.abort(); recognition.current = null; setListening(false); setInterim('') }
  function start() {
    if (!Constructor) { setError('This browser does not support dictation. Use the keyboard or your phone keyboard microphone.'); return }
    if (recognition.current) return
    setError(''); const r = new Constructor(); recognition.current = r
    r.lang = 'en-US'; r.continuous = true; r.interimResults = true
    r.onstart = () => setListening(true)
    r.onend = () => { setListening(false); recognition.current = null; setInterim('') }
    r.onerror = e => { setError(e.error === 'not-allowed' ? 'Microphone permission was not granted. You can still type.' : `Dictation stopped (${e.error}). You can try again.`); stop() }
    r.onresult = e => {
      let partial = '', final = ''
      for (let i = e.resultIndex; i < e.results.length; i++) { const result = e.results[i]; if (result.isFinal) final += result[0].transcript + ' '; else partial += result[0].transcript }
      setInterim(partial); if (final.trim()) callback.current(final.trim())
    }
    try { r.start() } catch { stop(); setError('The microphone could not be started. Check your browser permissions.') }
  }
  return { supported: !!Constructor, listening, interim, error, start, stop }
}
