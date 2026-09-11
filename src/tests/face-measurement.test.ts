import { describe, expect, it } from 'vitest'
import { validateFaceMeasurement } from '../blender/faceMeasurement'

describe('measurements bound to uploaded photo', () => {
  const value = { revision: 1 as const, width: 900, height: 1200, imageSha256: 'a'.repeat(64), points: Array.from({ length: 478 }, () => [.5, .4, -.02]) }
  it('preserves all points and rejects stale dimensions, hash and invalid coordinates', () => {
    expect(validateFaceMeasurement(value, 900, 1200, value.imageSha256)).toEqual(value)
    expect(() => validateFaceMeasurement(value, 800, 1200, value.imageSha256)).toThrow()
    expect(() => validateFaceMeasurement(value, 900, 1200, 'b'.repeat(64))).toThrow()
    expect(() => validateFaceMeasurement({ ...value, points: [[NaN, 0, 0], ...value.points.slice(1)] }, 900, 1200, value.imageSha256)).toThrow()
    expect(validateFaceMeasurement(undefined, 900, 1200, value.imageSha256)).toBeUndefined()
  })
})
