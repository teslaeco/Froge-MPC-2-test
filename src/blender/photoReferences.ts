export const MAX_REFERENCE_PHOTOS = 4
export const MAX_REFERENCE_BYTES = 2 * 1024 * 1024
export const MAX_PHOTO_REQUEST_BYTES = 9 * 1024 * 1024
export const MAX_TOTAL_REFERENCE_BYTES = 6 * 1024 * 1024
export const MAX_TOTAL_REFERENCE_PIXELS = 80 * 1024 * 1024
export type TextureMaxSize = 2048 | 4096 | 8192
export const PHOTO_VIEWS = { front: 'Przód', three_quarter: 'Trzy czwarte', side: 'Profil', back: 'Tył', detail: 'Detal', other: 'Inne ujęcie' } as const
export type PhotoView = keyof typeof PHOTO_VIEWS
export type PhotoInput = { name: string; view: PhotoView; dataUrl: string; subject?: string; textureMaxSize?: TextureMaxSize; faceLandmarks?: FaceMeasurement; faceMeasurementStatus?: string }
export type PhotoMetadata = { name: string; view: PhotoView; sha256: string; subject?: string; textureMaxSize?: TextureMaxSize; faceLandmarks?: FaceMeasurement }
export type JobPhoto = { name: string; view: PhotoView; url: string; subject?: string }
export const DEFAULT_PHOTO_PROMPT = 'Stwórz przybliżony model 3D głównego obiektu ze zdjęć. Dopasuj widoczne proporcje, kształt i kolory. Pomiń tło i napisy. Zbuduj rzeczywistą geometrię z materiałami i zapisz GLB.'

// Browser-normalized JPEGs only: no remote URLs, SVGs or oversized decoded images.
export function jpegDimensions(bytes: Uint8Array): [number, number] {
  if (bytes.length < 20 || bytes[0] !== 255 || bytes[1] !== 216 || bytes.at(-2) !== 255 || bytes.at(-1) !== 217) throw new Error('Nieprawidłowe zdjęcie JPEG.')
  let at = 2
  while (at + 9 < bytes.length) {
    if (bytes[at++] !== 255) break
    while (bytes[at] === 255) at++
    const marker = bytes[at++]
    if (marker === 218 || marker === 217) break
    const length = (bytes[at] << 8) | bytes[at + 1]
    if (length < 2 || at + length > bytes.length) break
    if ([192, 193, 194, 195, 197, 198, 199, 201, 202, 203, 205, 206, 207].includes(marker)) {
      const height = (bytes[at + 3] << 8) | bytes[at + 4], width = (bytes[at + 5] << 8) | bytes[at + 6]
      if (length < 8 || !width || !height || width > 8192 || height > 8192) throw new Error('Zdjęcie musi mieć maksymalnie 8192 pikseli na bok.')
      return [width, height]
    }
    at += length
  }
  throw new Error('Nie można odczytać wymiarów zdjęcia JPEG.')
}

export async function decodePhotoInputs(value: unknown) {
  if (value === undefined) return []
  if (!Array.isArray(value) || value.length > MAX_REFERENCE_PHOTOS) throw new Error('Dodaj maksymalnie 4 zdjęcia.')
  const photos: { input: PhotoInput; bytes: ArrayBuffer; metadata: PhotoMetadata }[] = []
  let totalBytes = 0, totalPixels = 0
  for (const item of value) {
    if (item?.textureMaxSize !== undefined && ![2048, 4096, 8192].includes(item.textureMaxSize)) throw new Error('Wybierz limit tekstur 2K, 4K lub 8K.')
    if (!item || typeof item !== 'object' || typeof item.name !== 'string' || !item.name.trim() || item.name.length > 120 || !Object.hasOwn(PHOTO_VIEWS, item.view) || typeof item.dataUrl !== 'string') throw new Error('Nieprawidłowy opis zdjęcia.')
    if (item.subject !== undefined && (typeof item.subject !== 'string' || item.subject.length > 160)) throw new Error('Opis osoby na zdjęciu może mieć do 160 znaków.')
    const match = /^data:image\/jpeg;base64,([A-Za-z0-9+/]+={0,2})$/.exec(item.dataUrl)
    if (!match || match[1].length > Math.ceil(MAX_REFERENCE_BYTES / 3) * 4) throw new Error('Zdjęcie jest nieprawidłowe lub za duże. Dodaj je ponownie.')
    let raw: string
    try { raw = atob(match[1]) } catch { throw new Error('Nieprawidłowy zapis zdjęcia.') }
    const bytes = Uint8Array.from(raw, character => character.charCodeAt(0))
    if (bytes.length > MAX_REFERENCE_BYTES) throw new Error('Zdjęcie jest za duże.')
    const [width, height] = jpegDimensions(bytes)
    totalBytes += bytes.length; totalPixels += width * height
    if (totalBytes > MAX_TOTAL_REFERENCE_BYTES || totalPixels > MAX_TOTAL_REFERENCE_PIXELS) throw new Error('Zdjęcia przekraczają wspólny limit 6 MB lub 80 megapikseli. Usuń jedno ujęcie albo wybierz mniejszą rozdzielczość.')
    const sha256 = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), x => x.toString(16).padStart(2, '0')).join('')
    const subject = item.subject?.trim() ? { subject: item.subject.trim() } : {}
    const faceLandmarks = validateFaceMeasurement(item.faceLandmarks, width, height, sha256)
    const quality = item.textureMaxSize === undefined ? {} : { textureMaxSize: item.textureMaxSize as TextureMaxSize }
    const measured = faceLandmarks ? { faceLandmarks } : {}
    const input = { name: item.name.trim(), view: item.view as PhotoView, dataUrl: item.dataUrl, ...subject, ...measured, ...quality }
    photos.push({ input, bytes: bytes.buffer, metadata: { name: input.name, view: input.view, sha256, ...subject, ...measured, ...quality } })
  }
  return photos
}

// Conservative letterbox detection. Keep a single broad picture band; never
// crop ordinary photos, tiny details, or a scene with several separate panels.
export function pictureBand(pixels: Uint8ClampedArray, width: number, height: number): [number, number] {
  const bands: [number, number][] = []; let start = -1
  for (let y = 0; y <= height; y++) {
    let lit = 0
    if (y < height) for (let x = 0; x < width; x++) {
      const at = (y * width + x) * 4
      if (Math.max(pixels[at], pixels[at + 1], pixels[at + 2]) > 30) lit++
    }
    if (lit > width * .25 && y < height) { if (start < 0) start = y }
    else if (start >= 0) { bands.push([start, y]); start = -1 }
  }
  const significant = bands.filter(([a, b]) => b - a > height * .1)
  if (significant.length !== 1) return [0, height]
  const [a, b] = significant[0]
  return b - a < height * .72 && a > height * .08 && b < height * .94
    ? [Math.max(0, a - 3), Math.min(height, b + 3)] : [0, height]
}

export async function prepareReferencePhoto(file: File, trimBorders = false, textureMaxSize: TextureMaxSize = 4096): Promise<PhotoInput> {
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) throw new Error('Wybierz zdjęcie JPG, PNG lub WebP.')
  if (!file.size || file.size > 12 * 1024 * 1024) throw new Error('Pojedynczy plik może mieć maksymalnie 12 MB.')
  const url = URL.createObjectURL(file)
  try {
    const image = new Image()
    await new Promise<void>((resolve, reject) => { image.onload = () => resolve(); image.onerror = () => reject(new Error('Nie można otworzyć zdjęcia.')); image.src = url })
    if (image.naturalWidth * image.naturalHeight > MAX_TOTAL_REFERENCE_PIXELS) throw new Error('Zdjęcie przekracza 80 megapikseli. Przygotuj mniejszy plik.')
    let top = 0, pictureHeight = image.naturalHeight
    if (trimBorders) {
      const sample = document.createElement('canvas'); sample.width = 256
      sample.height = Math.min(4096, Math.max(1, Math.round(image.naturalHeight * 256 / image.naturalWidth)))
      const sampler = sample.getContext('2d', { willReadFrequently: true })
      if (sampler) {
        sampler.drawImage(image, 0, 0, sample.width, sample.height)
        const [a, b] = pictureBand(sampler.getImageData(0, 0, sample.width, sample.height).data, sample.width, sample.height)
        top = Math.floor(a / sample.height * image.naturalHeight)
        pictureHeight = Math.min(image.naturalHeight - top, Math.ceil((b - a) / sample.height * image.naturalHeight))
      }
    }
    const scale = Math.min(1, textureMaxSize / Math.max(image.naturalWidth, pictureHeight))
    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, Math.round(image.naturalWidth * scale)); canvas.height = Math.max(1, Math.round(pictureHeight * scale))
    const context = canvas.getContext('2d')
    if (!context) throw new Error('Przeglądarka nie może przygotować zdjęcia.')
    context.fillStyle = '#ffffff'; context.fillRect(0, 0, canvas.width, canvas.height); context.drawImage(image, 0, top, image.naturalWidth, pictureHeight, 0, 0, canvas.width, canvas.height)
    for (const quality of [0.95, 0.90, 0.86]) {
      const dataUrl = canvas.toDataURL('image/jpeg', quality)
      if (dataUrl.startsWith('data:image/jpeg;base64,') && dataUrl.length - 23 <= Math.floor(MAX_REFERENCE_BYTES / 3) * 4) {
        let measurements: Pick<PhotoInput, 'faceLandmarks' | 'faceMeasurementStatus'>
        try { measurements = await (await import('./faceLandmarks')).measureFace(dataUrl) }
        catch { measurements = { faceMeasurementStatus: 'Pomiary twarzy są niedostępne. Zdjęcie pozostaje referencją wyglądu; dodaj je ponownie, aby ponowić pomiar.' } }
        return { name: file.name.slice(0, 120) || 'Zdjęcie', view: 'other', dataUrl, textureMaxSize, ...measurements }
      }
    }
    throw new Error('Zdjęcie przekracza 2 MB po przygotowaniu. Wybierz 4K lub 2K; nie obniżamy automatycznie jakości poniżej 86%.')
  } finally { URL.revokeObjectURL(url) }
}
import { validateFaceMeasurement, type FaceMeasurement } from './faceMeasurement'
