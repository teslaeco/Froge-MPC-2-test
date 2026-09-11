import { useRef, useState } from 'react'
import { MAX_REFERENCE_PHOTOS, PHOTO_VIEWS, prepareReferencePhoto, type PhotoInput, type PhotoView, type TextureMaxSize } from './photoReferences'

export function PhotoReferences({ photos, onChange, disabled, onPreparing }: { photos: PhotoInput[]; onChange: (photos: PhotoInput[]) => void; disabled: boolean; onPreparing: (busy: boolean) => void }) {
  const [preparing, setPreparing] = useState(false), [error, setError] = useState('')
  const [trimBorders, setTrimBorders] = useState(false)
  const [textureMaxSize, setTextureMaxSize] = useState<TextureMaxSize>(4096)
  const selecting = useRef(false)
  async function add(files: FileList | null) {
    if (!files?.length || selecting.current || disabled) return
    selecting.current = true; setPreparing(true); onPreparing(true); setError('')
    try {
      const chosen = Array.from(files)
      if (photos.length + chosen.length > MAX_REFERENCE_PHOTOS) throw new Error('Możesz dołączyć maksymalnie 4 zdjęcia. Usuń jedno, aby dodać kolejne.')
      const next = [...photos]
      for (const file of chosen) {
        const photo = await prepareReferencePhoto(file, trimBorders, textureMaxSize)
        next.push({ ...photo, view: next.length === 0 ? 'front' : 'other' })
      }
      onChange(next)
    } catch (e) { setError((e as Error).message) }
    finally { selecting.current = false; setPreparing(false); onPreparing(false) }
  }
  return <section className="photo-references" aria-label="Zdjęcia do modelu 3D">
    <h3>Model 3D ze zdjęć</h3>
    <p>Dodaj 1–4 ujęcia tej samej postaci lub obiektu. Inną modelkę generuj w osobnym zleceniu. Zdjęcie z tyłu pomaga odtworzyć plecy i fryzurę.</p>
    <label>Rozmiar przesyłanego zdjęcia<select value={textureMaxSize} disabled={disabled || preparing} onChange={e => setTextureMaxSize(Number(e.target.value) as TextureMaxSize)}><option value={2048}>Do 2K</option><option value={4096}>Do 4K</option><option value={8192}>Do 8K</option></select></label>
    <label><input type="checkbox" checked={trimBorders} disabled={disabled || preparing} onChange={e => setTrimBorders(e.target.checked)}/> Usuń czarne pasy przy dodawaniu kadru</label>
    <label className="photo-picker">Dodaj zdjęcia · JPG, PNG, WebP
      <input type="file" accept="image/jpeg,image/png,image/webp" multiple disabled={disabled || preparing || photos.length >= MAX_REFERENCE_PHOTOS} onChange={event => { void add(event.target.files); event.target.value = '' }}/>
    </label>
    <p className="studio-helper">Do 12 MB na plik źródłowy, 2 MB po przygotowaniu i 6 MB na zlecenie. Zdjęcia zachowują proporcje i nie są powiększane. Rozdzielczość generowanych tekstur wybierasz osobno w ustawieniach Meshy. Zapis i wysłanie zdjęć następują po kliknięciu „Generuj”.</p>
    {preparing && <p role="status">Przygotowuję zdjęcia…</p>}
    <div className="photo-reference-grid">{photos.map((photo, index) => <div className="photo-reference" key={index}>
      <img src={photo.dataUrl} alt={`Zdjęcie referencyjne ${index + 1}: ${photo.name}`}/>
      <span title={photo.name}>{photo.name}</span>
      {photo.textureMaxSize && <small>Zdjęcie do {photo.textureMaxSize / 1024}K · z dostępnych pikseli</small>}
      <label>Ujęcie {index + 1}<select value={photo.view} disabled={disabled || preparing} onChange={event => onChange(photos.map((item, i) => i === index ? { ...item, view: event.target.value as PhotoView } : item))}>{Object.entries(PHOTO_VIEWS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label>Osoba lub element<input maxLength={160} value={photo.subject || ''} disabled={disabled || preparing} placeholder="Np. osoba pośrodku, kręcone włosy" onChange={e => onChange(photos.map((item, i) => i === index ? { ...item, subject: e.target.value } : item))}/></label>
      <button type="button" disabled={disabled || preparing} onClick={() => onChange(photos.filter((_, i) => i !== index))} aria-label={`Usuń zdjęcie ${index + 1}`}>Usuń zdjęcie</button>
    </div>)}</div>
    {photos.length > 1 && <p className="studio-helper">Każde ujęcie powinno pokazywać ten sam strój i tę samą postać. Oznacz przód, profil i tył; nie mieszaj zdjęć różnych osób.</p>}
    {error && <p role="alert" className="studio-error">{error}</p>}
  </section>
}
