import { useState } from 'react'
import { blenderRequest, type BlenderConnection } from './client'

export const oracleOpenAIUpdateCommand = `scp -o IdentitiesOnly=yes -i "$HOME/ssh-key-2026-09-06.key" "$HOME/froge-oracle-openai.zip" opc@141.148.242.30:/home/opc/froge-oracle-openai.zip &&
ssh -T -o IdentitiesOnly=yes -o ConnectTimeout=20 -i "$HOME/ssh-key-2026-09-06.key" opc@141.148.242.30 'python3 -m zipfile -e "$HOME/froge-oracle-openai.zip" "$HOME/froge-openai-update" && python3 "$HOME/froge-openai-update/apply_update.py"'`

export const oracleRebuildUpdateCommand = oracleOpenAIUpdateCommand.replaceAll('froge-oracle-openai.zip', 'froge-oracle-rebuild.zip').replaceAll('froge-openai-update', 'froge-rebuild-update')
export const oracleGeometryUpdateCommand = oracleOpenAIUpdateCommand.replaceAll('froge-oracle-openai.zip', 'froge-oracle-wardrobe-v9.zip').replaceAll('froge-openai-update', 'froge-wardrobe-v9-update')

export function GeometryUpdate() {
  return <div className="blender-setup">
    <strong>Zaktualizuj generator na Oracle</strong>
    <p>Wersja 9 dodaje wyraźniejszy krój ubrań, kieszenie, fałdy i sneakersy z podeszwami oraz sznurowaniem.</p>
    <a href="/downloads/froge-oracle-wardrobe-v9.zip" download>Pobierz aktualizację generatora</a>
    <details><summary>Jak zainstalować aktualizację?</summary><p>Prześlij ZIP w Oracle Cloud Shell przez Menu → Upload. Po Completed wklej:</p><pre tabIndex={0}>{oracleGeometryUpdateCommand}</pre><p>Po FROGE_UPDATE_OK odśwież stronę i utwórz nowy model. Zapisany klucz OpenAI i połączenie zostają zachowane.</p></details>
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
    <p>OpenAI przygotuje instrukcje modelu, a Blender wykona je na Oracle. Najpierw zaktualizuj program na serwerze.</p>
    <a href="/downloads/froge-oracle-openai.zip" download>Pobierz aktualizację OpenAI</a>
    <details><summary>Jak zaktualizować Oracle?</summary><p>Anuluj aktywne zlecenie. W Oracle Cloud Shell wybierz Menu → Upload i prześlij pobrany ZIP. Następnie wklej to polecenie:</p><pre tabIndex={0}>{oracleOpenAIUpdateCommand}</pre><p>Po FROGE_UPDATE_OK odśwież stronę i podłącz klucz API w tym miejscu.</p></details>
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
