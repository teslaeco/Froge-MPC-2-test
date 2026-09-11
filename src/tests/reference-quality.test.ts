import { expect, it } from 'vitest'
import { decodePhotoInputs, jpegDimensions } from '../blender/photoReferences'

const jpeg = (width: number, height: number) => new Uint8Array([255,216,255,192,0,11,8,height>>8,height&255,width>>8,width&255,1,1,17,0,255,218,0,2,0,255,217])
const photo = (width = 8192, height = 4096) => ({ name:'original.jpg', view:'front', textureMaxSize:8192,
  dataUrl:'data:image/jpeg;base64,'+btoa(String.fromCharCode(...jpeg(width,height))) })

it('preserves admitted 8K bytes and quality metadata through the browser API', async () => {
  const [decoded] = await decodePhotoInputs([photo()])
  expect(new Uint8Array(decoded.bytes)).toEqual(jpeg(8192,4096))
  expect(decoded.metadata.textureMaxSize).toBe(8192)
  expect(decoded.input.textureMaxSize).toBe(8192)
  expect(decoded.metadata.sha256).toMatch(/^[a-f0-9]{64}$/)
})
it('rejects excess decoded pixels and unsupported texture sizes before admission', async () => {
  await expect(decodePhotoInputs([photo(),photo(),photo()])).rejects.toThrow('80 megapikseli')
  await expect(decodePhotoInputs([{...photo(),textureMaxSize:8193}])).rejects.toThrow('limit tekstur')
  expect(() => jpegDimensions(jpeg(8193,2))).toThrow('8192')
})
