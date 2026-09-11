import { useEffect, useState } from 'react'
import { blenderRequest } from './client'

const labels: Record<string, string> = { master: 'Pełny GLB · oryginalna jakość', fbx: 'FBX', pbr: 'Oryginalne mapy PBR (ZIP)', obj: 'OBJ + MTL + tekstury (ZIP)', stl: 'STL · mm', blend: 'Blender', 'scene-json': 'Plan sceny JSON' }
type Exports = { formats: { format: string; bytes: number }[]; quality?: { texturesReduced?: boolean; masterTextures?: { name: string; size: number[] }[] } }
export function GenerationExports({ jobId }: { jobId: string }) {
  const [data, setData] = useState<Exports | null>(null), [error, setError] = useState('')
  useEffect(() => {
    const controller = new AbortController()
    setData(null); setError('')
    void blenderRequest<Exports>(`jobs/${jobId}/exports`, { signal: controller.signal })
      .then(result => { if (!Array.isArray(result.formats)) throw new Error('Brak listy eksportów. Sprawdź aktualizację serwera.'); if (!controller.signal.aborted) setData(result) })
      .catch(e => { if (!controller.signal.aborted) setError((e as Error).message) })
    return () => controller.abort()
  }, [jobId])
  if (error) return <p role="status">Eksporty na Oracle: {error}</p>
  if (!data) return <p role="status">Sprawdzam pliki do pobrania…</p>
  return <div className="generation-exports" aria-label="Pliki wygenerowanego modelu">
    <strong>Pobierz model</strong>
    {data.quality?.texturesReduced && <p>Podgląd ma mniejsze tekstury. Pełny GLB i FBX zachowują tekstury modelu źródłowego.</p>}
    <ul>{data.formats.filter(f => labels[f.format]).map(f => <li key={f.format}><a href={`/api/blender/jobs/${jobId}/exports/${f.format}`} download>{labels[f.format]} · {(f.bytes / 1024**2).toFixed(1)} MB</a></li>)}</ul>
    {!!data.quality?.masterTextures?.length && <details><summary>Rzeczywiste rozmiary tekstur</summary><ul>{data.quality.masterTextures.map((t, i) => <li key={i}>{t.name}: {t.size.join(' × ')} px</li>)}</ul></details>}
  </div>
}
