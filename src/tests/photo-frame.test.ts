import { expect,it } from 'vitest'
import { pictureBand } from '../blender/photoReferences'
function image(bands:[number,number][]) {
  const pixels=new Uint8ClampedArray(100*300*4)
  for(const [a,b] of bands)for(let y=a;y<b;y++)for(let x=0;x<100;x++)pixels[(y*100+x)*4]=100
  return pixels
}
it('uses the movie picture rather than the black screenshot borders',()=>{
  expect(pictureBand(image([[125,185]]),100,300)).toEqual([122,188])
})
it('preserves ordinary photos and multiple separate pictures',()=>{
  expect(pictureBand(image([[0,300]]),100,300)).toEqual([0,300])
  expect(pictureBand(image([[30,100],[140,230]]),100,300)).toEqual([0,300])
})
