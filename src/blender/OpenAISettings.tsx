import { useState } from 'react'
import { blenderRequest, type BlenderConnection } from './client'

export const oracleOpenAIUpdateCommand = `scp -o IdentitiesOnly=yes -i "$HOME/ssh-key-2026-09-06.key" "$HOME/froge-oracle-openai.zip" opc@141.148.242.30:/home/opc/froge-oracle-openai.zip &&
ssh -T -o IdentitiesOnly=yes -o ConnectTimeout=20 -i "$HOME/ssh-key-2026-09-06.key" opc@141.148.242.30 'python3 -m zipfile -e "$HOME/froge-oracle-openai.zip" "$HOME/froge-openai-update" && python3 "$HOME/froge-openai-update/apply_update.py"'`

export const oracleRebuildUpdateCommand = oracleOpenAIUpdateCommand.replaceAll('froge-oracle-openai.zip', 'froge-oracle-rebuild.zip').replaceAll('froge-openai-update', 'froge-rebuild-update')
export const oracleGeometryUpdateCommand = oracleOpenAIUpdateCommand.replaceAll('froge-oracle-openai.zip', 'froge-oracle-update.zip').replaceAll('froge-openai-update', 'froge-photos-v14-update')
export const oracleRepairCommand = 'python3 "$HOME/froge-napraw-oracle.py"'
export const portraitUpdateCommand = 'python3 -m zipfile -e "$HOME/froge-v20.zip" "$HOME/froge-v20"\npython3 "$HOME/froge-v20/froge-v20.py"'

export function GeometryUpdate({ required = true }: { required?: boolean }) {
  const [copyNote, setCopyNote] = useState('')
  return <div className="blender-setup">
    <strong>{required ? 'Włącz generator postaci · v20' : 'Pełna aktualizacja generatora · v20'}</strong>
    <p>Dopasowana suknia, cienkie zdobienia i wachlarz z wirnikami. Zachowane sceny do 3 postaci, fryzury, zdjęcia oraz pełne pliki geometrii i tekstur. Anatomiczna twarz z teksturą 2048 px, osobne oczy, pięć palców i paznokcie na każdej dłoni. Generator sprawdza te elementy przed zapisaniem wyniku. Podobieństwo do zdjęcia nadal wymaga oceny w podglądzie.</p>
    <a href="/downloads/froge-v20.zip" download>Pobierz pełną paczkę · v20</a>
    <details open={required}><summary>Jak włączyć standard?</summary><p>Prześlij ZIP do Oracle Cloud Shell przez Menu → Upload. Po Completed wklej:</p><pre tabIndex={0}>{portraitUpdateCommand}</pre><button onClick={() => { if (!navigator.clipboard) { setCopyNote('Zaznacz polecenie powyżej i skopiuj ręcznie.'); return } void navigator.clipboard.writeText(portraitUpdateCommand).then(() => setCopyNote('Skopiowano polecenie aktualizacji.'), () => setCopyNote('Zaznacz polecenie powyżej i skopiuj ręcznie.')) }}>Kopiuj polecenie aktualizacji</button>{copyNote && <p role="status">{copyNote}</p>}<p>Instalator zachowuje połączenie i modele, tworzy kopię programu i sprawdza prawdziwy eksport GLB bez zapytania do AI. Po FROGE_V20_OK kliknij „Sprawdź serwer po aktualizacji”.</p></details>
  </div>
}

export function SavedScriptUpdate() {
  return <div className="blender-setup">
    <strong>Wykorzystaj zapisany skrypt</strong>
    <p>Aktualizacja przywraca gotową funkcję materiałów i pozwala ponownie wykonać skrypt bez czekania na AI.</p>
    <a href="/downloads/froge-oracle-rebuild.zip" download>Pobierz poprawkę materiałów</a>
    <details><summary>Jak zainstalować poprawkę?</summary><p>Prześlij ZIP do Oracle Cloud Shell przez Menu → Upload. Poczekaj na Completed i wklej:</p><pre tabIndex={0}>{oracleRebuildUpdateCommand}</pre><p>Po FROGE_UPDATE_OK odśwież stronę i wybierz „Wykonaj zapisany skrypt”.</p></details>
  </div>
}

export function OpenAISettings({ connection, busy, onSaved }: { connection: BlenderConnection; busy: boolean; onSaved: () => Promise<void> }) {
  const [apiKey, setApiKey] = useState(''), [saving, setSaving] = useState(false), [note, setNote] = useState('')
  async function save(provider: 'openai' | 'ollama') {
    setSaving(true); setNote('')
    const value = apiKey.trim()
    try {
      await blenderRequest('ai', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ provider, ...(value && provider === 'openai' ? { apiKey: value } : {}) }) })
      setApiKey('')
      await onSaved()
      setNote(provider === 'openai' ? 'OpenAI podłączone. Możesz wygenerować model.' : 'Wybrano lokalne AI.')
    } catch (error) { setNote((error as Error).message) }
    finally { setSaving(false) }
  }
  if ((connection.connectorVersion || 1) < 4) return <div className="blender-setup">
    <strong>OpenAI · Astra</strong>
    <p>Połączony generator jest zbyt stary, aby wybrać OpenAI. Uruchom aktualizację v14 z instrukcji powyżej i sprawdź serwer ponownie.</p>
  </div>
  return <div className="blender-setup">
    <strong>OpenAI · Astra</strong>
    <p>{connection.provider === 'openai' ? 'Generowanie korzysta z OpenAI API.' : 'Teraz działa lokalny Qwen. Podłącz OpenAI, aby przenieść tworzenie instrukcji do Astry.'}</p>
    <label>Klucz API OpenAI<input type="password" value={apiKey} onChange={event => setApiKey(event.target.value)} placeholder={connection.provider === 'openai' ? 'Klucz zapisany — wpisz tylko, aby go zmienić' : 'sk-…'} autoComplete="off" autoCapitalize="none" autoCorrect="off" spellCheck={false} maxLength={503}/></label>
    <p>To płatne API rozliczane na Twoim koncie OpenAI. Klucz jest zapisywany na Twoim serwerze Oracle. <a href="https://platform.openai.com/api-keys" target="_blank" rel="noreferrer">Klucze API</a> · <a href="https://developers.openai.com/api/docs/models/gpt-6-astra" target="_blank" rel="noreferrer">Cennik Astry</a></p>
    <button disabled={busy || saving || !apiKey.trim()} onClick={() => void save('openai')}>{saving ? 'Sprawdzam połączenie…' : 'Podłącz OpenAI'}</button>
    {connection.provider === 'openai' && <button disabled={busy || saving} onClick={() => void save('ollama')}>Przełącz na lokalne AI</button>}
    {busy && <p>Zatrzymaj bieżące generowanie przed zmianą AI.</p>}
    {note && <p role="status">{note}</p>}
  </div>
}
