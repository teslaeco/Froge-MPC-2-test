import { describe,expect,it } from 'vitest'
import { supportsPortraitQuality,requiresPortraitQuality } from '../blender/compatibility'

describe('portrait quality admission',()=>{
  it('requires the worker capability, not just an updated website or a version label',()=>{
    expect(supportsPortraitQuality({connectorVersion:14,portraitRevision:1})).toBe(false)
    expect(supportsPortraitQuality({connectorVersion:15})).toBe(false)
    expect(supportsPortraitQuality({connectorVersion:15,portraitRevision:1})).toBe(true)
  })
  it('protects human and photo jobs while keeping old object generation available',()=>{
    expect(requiresPortraitQuality('Dziewczyna siedząca ze zdjęcia')).toBe(true)
    expect(requiresPortraitQuality('Odwzoruj załącznik',1)).toBe(true)
    expect(requiresPortraitQuality('Dąb dla Cardi B')).toBe(false)
    expect(requiresPortraitQuality('Rakieta')).toBe(false)
  })
})
