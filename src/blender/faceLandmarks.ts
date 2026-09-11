import { FaceLandmarker, FilesetResolver } from '@mediapipe/tasks-vision'
import type { FaceMeasurement } from './faceMeasurement'

let detector: Promise<FaceLandmarker> | undefined
const getDetector = () => detector ??= FilesetResolver.forVisionTasks('/face-fit').then(files =>
  FaceLandmarker.createFromOptions(files, {
    baseOptions: { modelAssetPath: '/face-fit/face_landmarker.task', delegate: 'CPU' },
    runningMode: 'IMAGE', numFaces: 2,
  })).catch(error => { detector = undefined; throw error })

// Detect the compressed, EXIF-normalized JPEG that is actually uploaded.
// Model files are served by our Site; the photo never goes to an ML vendor.
export async function measureFace(dataUrl: string): Promise<{ faceLandmarks?: FaceMeasurement; faceMeasurementStatus: string }> {
  const blob = await (await fetch(dataUrl)).blob()
  const bytes = await blob.arrayBuffer()
  const imageSha256 = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), n => n.toString(16).padStart(2, '0')).join('')
  const bitmap = await createImageBitmap(blob)
  try {
    const model = await getDetector()
    const result = model.detect(bitmap)
    if (result.faceLandmarks.length !== 1) return { faceMeasurementStatus: result.faceLandmarks.length > 1
      ? 'Kilka twarzy — do dopasowania dodaj osobne zbliżenie.' : 'Nie odczytano twarzy — zdjęcie pozostaje referencją wyglądu.' }
    return { faceLandmarks: { revision: 1, width: bitmap.width, height: bitmap.height, imageSha256,
      points: result.faceLandmarks[0].map(p => [p.x, p.y, p.z].map(n => Number(n.toFixed(7)))) },
      faceMeasurementStatus: 'Odczytano 478 punktów twarzy. Dopasowanie obsługuje jedną postać kobiecą.' }
  } finally { bitmap.close() }
}
