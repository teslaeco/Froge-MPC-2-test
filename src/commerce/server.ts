import { productSchema } from './domain'
import { sceneSchema } from '../studio/scene'
type Row={id:string;payload:string;revision:number;updated:string}
type Statement={bind:(...args:unknown[])=>Statement;all:<T>()=>Promise<{results:T[]}>;first:<T>()=>Promise<T|null>;run:()=>Promise<{meta:{changes?:number}}>}
export type CommerceEnv={DB?:{prepare:(sql:string)=>Statement};BUCKET?:{put:(key:string,value:ArrayBuffer,options?:unknown)=>Promise<unknown>;get:(key:string)=>Promise<{body:ReadableStream}|null>;head:(key:string)=>Promise<unknown>}}
const response=(data:unknown,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store'}})
const uuid=/^[a-f0-9-]{36}$/
class PayloadLimit extends Error{}
async function boundedBody(request:Request,limit:number){
 if(Number(request.headers.get('content-length'))>limit)throw new PayloadLimit()
 const reader=request.body?.getReader();if(!reader)return new ArrayBuffer(0)
 const chunks:Uint8Array[]=[];let total=0
 for(;;){const {value,done}=await reader.read();if(done)break;total+=value.byteLength;if(total>limit){await reader.cancel();throw new PayloadLimit()}chunks.push(value)}
 const buffer=new Uint8Array(total);let offset=0;for(const chunk of chunks){buffer.set(chunk,offset);offset+=chunk.length}return buffer.buffer
}
export async function commerceApi(request:Request,env:CommerceEnv):Promise<Response>{
  const url=new URL(request.url),owner=request.headers.get('oai-authenticated-user-id')
  if(!owner)return response({error:'Zaloguj się do platformy, aby otworzyć swój katalog.'},401)
  if(request.method!=='GET'&&request.headers.get('origin')!==url.origin)return response({error:'Niedozwolone źródło zapisu.'},403)
  const db=env.DB
  if(!db)return response({error:'Katalog jest chwilowo niedostępny. Zachowaj otwarty formularz i spróbuj ponownie.'},503)
  try{
    if(url.pathname==='/api/commerce/products'){
      if(request.method==='GET'){
        const data=await db.prepare('SELECT id,payload,revision,updated FROM commerce_products WHERE owner=? ORDER BY updated DESC LIMIT 501').bind(owner).all<Row>()
        return response({products:data.results.map(row=>({...JSON.parse(row.payload),revision:row.revision,updated:row.updated}))})
      }
      if(request.method!=='PUT')return response({error:'Niedozwolona metoda.'},405)
      if(!request.headers.get('content-type')?.startsWith('application/json'))return response({error:'Wymagany format JSON.'},415)
      const text=new TextDecoder().decode(await boundedBody(request,40000))
      const input=JSON.parse(text) as {product:unknown;revision:unknown}
      const parsed=productSchema.safeParse(input.product)
      if(!parsed.success||!Number.isSafeInteger(input.revision)||Number(input.revision)<0)return response({error:'Sprawdź pola produktu i wartości liczbowe.'},400)
      const p=parsed.data, revision=Number(input.revision),updated=new Date().toISOString()
      if(p.modelFile&&(!env.BUCKET||!await env.BUCKET.head(`${owner}/${p.modelFile}`)))return response({error:'Załączony model nie istnieje. Prześlij go ponownie.'},400)
      if(revision===0){
        const count=await db.prepare('SELECT COUNT(*) AS total FROM commerce_products WHERE owner=?').bind(owner).first<{total:number}>()
        if((count?.total??0)>=500)return response({error:'Katalog osiągnął limit 500 produktów.'},409)
        const result=await db.prepare('INSERT INTO commerce_products (id,owner,payload,revision,updated) VALUES (?,?,?,1,?) ON CONFLICT(id) DO NOTHING').bind(p.id,owner,JSON.stringify(p),updated).run()
        if(result.meta.changes!==1)return response({error:'Produkt już zapisano. Odśwież katalog przed dalszą edycją.'},409)
      }else{
        const result=await db.prepare('UPDATE commerce_products SET payload=?,revision=revision+1,updated=? WHERE id=? AND owner=? AND revision=?').bind(JSON.stringify(p),updated,p.id,owner,revision).run()
        if(result.meta.changes!==1)return response({error:'Produkt zmienił się w innej karcie. Skopiuj swoje zmiany i odśwież katalog.'},409)
      }
      return response({product:{...p,revision:revision+1,updated}})
    }
    if(url.pathname==='/api/commerce/models'&&request.method==='POST'){
      if(!env.BUCKET)return response({error:'Przechowywanie modeli jest chwilowo niedostępne.'},503)
      const bytes=await boundedBody(request,12*1024*1024);if(bytes.byteLength<12)return response({error:'Model musi mieć od 12 bajtów do 12 MB.'},413)
      const isJson=request.headers.get('content-type')==='application/json'
      if(isJson){const result=sceneSchema.safeParse(JSON.parse(new TextDecoder().decode(bytes)));if(!result.success)return response({error:'Nieprawidłowy model Froge JSON. Wyeksportuj go ze studia 3D.'},400)}
      else{const h=new DataView(bytes);if(h.getUint32(0,true)!==0x46546c67||h.getUint32(4,true)!==2||h.getUint32(8,true)!==bytes.byteLength)return response({error:'Wybierz prawidłowy plik GLB 2.0 albo Froge JSON.'},400)}
      const filename=`${crypto.randomUUID()}.${isJson?'json':'glb'}`
      await env.BUCKET.put(`${owner}/${filename}`,bytes)
      return response({filename})
    }
    const file=url.pathname.match(/^\/api\/commerce\/models\/([a-f0-9-]{36}\.(?:glb|json))$/)
    if(file&&request.method==='GET'){
      if(!uuid.test(file[1].split('.')[0])||!env.BUCKET)return response({error:'Model niedostępny.'},404)
      const object=await env.BUCKET.get(`${owner}/${file[1]}`)
      if(!object)return response({error:'Nie znaleziono modelu.'},404)
      return new Response(object.body,{headers:{'Content-Type':file[1].endsWith('.json')?'application/json':'model/gltf-binary','Cache-Control':'private, no-store','Content-Disposition':`attachment; filename="${file[1]}"`,'X-Content-Type-Options':'nosniff'}})
    }
    return response({error:'Nie znaleziono funkcji.'},404)
  }catch(error){
    if(error instanceof PayloadLimit)return response({error:'Plik lub opis przekracza dozwolony rozmiar.'},413)
    if(error instanceof SyntaxError)return response({error:'Nieprawidłowy plik JSON.'},400)
    console.error('Commerce storage request failed',error instanceof Error?error.message:'unknown')
    return response({error:'Nie udało się odczytać lub zapisać danych. Formularz pozostaje otwarty; spróbuj ponownie.'},503)
  }
}
