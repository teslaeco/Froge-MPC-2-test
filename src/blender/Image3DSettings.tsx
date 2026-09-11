import { useState } from 'react'
import { blenderRequest, type BlenderConnection } from './client'

export function Image3DSettings({ connection, busy, onSaved }: { connection: BlenderConnection; busy: boolean; onSaved: () => Promise<void> }) {
  const [apiKey, setApiKey] = useState('')
  const [resolution, setResolution] = useState<'4k' | '8k'>(connection.image3dTextureResolution || '8k')
  const [saving, setSaving] = useState(false), [note, setNote] = useState('')
  async function save() {
    setSaving(true); setNote('')
    try {
      await blenderRequest('image3d', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: 'meshy', textureResolution: resolution, ...(apiKey.trim() ? { apiKey: apiKey.trim() } : {}) }) })
      setApiKey(''); await onSaved()
      setNote('Meshy podłączone. Sam zapis ustawień nie generuje płatnego modelu.')
    } catch (error) { setNote((error as Error).message) }
    finally { setSaving(false) }
  }
  return <section className="blender-setup" aria-label="Ustawienia zdjęć do 3D">
    <strong>Zdjęcia → 3D · Meshy 7 Ultra</strong>
    <p>Generuje geometrię i tekstury z przesłanych zdjęć. Jedno zlecenie tworzy jedną postać lub obiekt; możesz dodać do czterech jego ujęć.</p>
    {(connection.connectorVersion || 0) < 21 ? <p>Najpierw zainstaluj aktualizację v21 na Oracle. Dotychczasowy generator ze zdjęć korzystał z gotowej anatomii.</p> : <>
      <label>Klucz API Meshy<input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} autoComplete="off" autoCapitalize="none" autoCorrect="off" spellCheck={false} maxLength={512} placeholder={connection.image3dReady ? 'Klucz zapisany — wpisz tylko, aby go zmienić' : 'Klucz z konta Meshy'}/></label>
      <label>Tekstura koloru<select value={resolution} onChange={e => setResolution(e.target.value as '4k' | '8k')} disabled={busy || saving}><option value="8k">8K · Ultra</option><option value="4k">4K · Ultra</option></select></label>
      <p>To osobne, płatne API na Twoim koncie Meshy. Klucz OpenAI go nie zastępuje. <a href="https://www.meshy.ai/" target="_blank" rel="noreferrer">Konto Meshy</a> · <a href="https://docs.meshy.ai/en/api/pricing" target="_blank" rel="noreferrer">Cennik API</a></p>
      <p>Zdjęcia posłużą geometrii i teksturom. Niewidoczne powierzchnie są rekonstruowane; zgodność twarzy i tyłu oceń w podglądzie. Pełne pliki zachowują jakość otrzymaną z silnika.</p>
      <button disabled={busy || saving || (!apiKey.trim() && !connection.image3dReady)} onClick={() => void save()}>{saving ? 'Sprawdzam połączenie…' : connection.image3dReady ? 'Zapisz jakość zdjęć → 3D' : 'Podłącz Meshy'}</button>
    </>}
    {note && <p role="status">{note}</p>}
  </section>
}
