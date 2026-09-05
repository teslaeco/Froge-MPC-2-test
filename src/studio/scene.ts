import { z } from 'zod'
import { BufferGeometry, DataTexture, Float32BufferAttribute, Group, Mesh, MeshStandardMaterial, RepeatWrapping, SRGBColorSpace } from 'three'
const partSchema = z.object({name:z.string().min(1).max(100),vertices:z.array(z.number().finite().min(-10000).max(10000)).min(9).max(150000),triangles:z.array(z.number().int().nonnegative()).min(3).max(300000),uv:z.array(z.number().finite().min(-1000).max(1000)).max(100000),color:z.string().regex(/^#[0-9a-f]{6}$/i),roughness:z.number().min(0).max(1),metalness:z.number().min(0).max(1),pattern:z.enum(['solid','scales','bark'])}).strict()
export const sceneSchema = z.object({version:z.literal(1),name:z.string().min(1).max(160),description:z.string().max(2000),parts:z.array(partSchema).min(1).max(256)}).strict().superRefine((scene, context) => {
  let total=0
  scene.parts.forEach((part,i)=>{total+=part.vertices.length;if(part.vertices.length%3 || part.triangles.length%3 || part.uv.length!==part.vertices.length/3*2 || part.triangles.some(v=>v>=part.vertices.length/3)) context.addIssue({code:'custom',path:['parts',i],message:'Nieprawidłowe indeksy, UV lub liczba wierzchołków.'})})
  if(total>600000) context.addIssue({code:'custom',message:'Model przekracza limit 200 000 wierzchołków.'})
})
export type ModelScene=z.infer<typeof sceneSchema>
export function sceneTexture(color:string,pattern:ModelScene['parts'][number]['pattern']) {
  const data=new Uint8Array(128*128*4),rgb=[1,3,5].map(i=>parseInt(color.slice(i,i+2),16))
  for(let y=0;y<128;y++) for(let x=0;x<128;x++) {
    let factor=1
    if(pattern==='scales'){const xx=((x+(Math.floor(y/16)%2)*8)%16-8)/8,yy=(y%16)/16;factor=xx*xx+yy*yy>.86?.55:.92+.08*(1-yy)}
    if(pattern==='bark')factor=.58+.42*(.5+.5*Math.sin(x*.65+Math.sin(y*.15)*2))
    const index=(y*128+x)*4;for(let i=0;i<3;i++)data[index+i]=Math.round(rgb[i]*factor);data[index+3]=255
  }
  const texture=new DataTexture(data,128,128);texture.colorSpace=SRGBColorSpace;texture.wrapS=texture.wrapT=RepeatWrapping;texture.needsUpdate=true;return texture
}
export function sceneModel(value:unknown):Group {
  const scene=sceneSchema.parse(value),group=new Group();group.name=scene.name
  for(const part of scene.parts){const geometry=new BufferGeometry();geometry.setAttribute('position',new Float32BufferAttribute(part.vertices.map(v=>v/100),3));geometry.setIndex(part.triangles);geometry.setAttribute('uv',new Float32BufferAttribute(part.uv,2));geometry.computeVertexNormals();const material=new MeshStandardMaterial({map:sceneTexture(part.color,part.pattern),roughness:part.roughness,metalness:part.metalness});const mesh=new Mesh(geometry,material);mesh.name=part.name;group.add(mesh)}
  return group
}
