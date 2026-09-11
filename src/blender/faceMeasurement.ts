export type FaceMeasurement = { revision: 1; width: number; height: number; imageSha256: string; points: number[][] }

export function validateFaceMeasurement(value: unknown, width: number, height: number, sha256: string): FaceMeasurement | undefined {
  if (value === undefined) return undefined
  const v = value as FaceMeasurement
  if (!v || v.revision !== 1 || v.width !== width || v.height !== height || v.imageSha256 !== sha256 ||
      !Array.isArray(v.points) || v.points.length !== 478 || v.points.some(p => !Array.isArray(p) || p.length !== 3 || p.some(x => typeof x !== 'number' || !Number.isFinite(x) || Math.abs(x) > 2))) {
    throw new Error('Pomiary twarzy nie pasują do zdjęcia. Dodaj je ponownie.')
  }
  return { revision: 1, width, height, imageSha256: sha256, points: v.points }
}
