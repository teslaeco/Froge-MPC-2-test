// Static application plus explicit retirement of the former paid provider routes.
import { commerceApi, type CommerceEnv } from '../commerce/server'
import { blenderApi, type BlenderEnv } from '../blender/server'
type Environment=CommerceEnv & BlenderEnv & {ASSETS:{fetch:(request:Request)=>Promise<Response>}}
export default {async fetch(request:Request,env:Environment):Promise<Response>{
 const url=new URL(request.url)
 if(url.pathname.startsWith('/api/blender/'))return blenderApi(request,env)
 if(url.pathname.startsWith('/api/commerce/'))return commerceApi(request,env)
 if(url.pathname.startsWith('/api/3d/'))return Response.json({error:'Płatny generator został usunięty. Użyj Codexa lub dodatku Blender z lokalnym AI.'},{status:410,headers:{'Cache-Control':'no-store'}})
 let result=await env.ASSETS.fetch(request)
 if(result.status===404&&request.method==='GET'&&request.headers.get('accept')?.includes('text/html'))result=await env.ASSETS.fetch(new Request(new URL('/index.html',url),request))
 // The entry document must pick up the current hashed bundle after an update.
 // Preserve caching for versioned JavaScript, images and downloadable models.
 if(result.headers.get('content-type')?.includes('text/html')){
  const headers=new Headers(result.headers)
  headers.set('Cache-Control','private, no-store')
  return new Response(result.body,{status:result.status,statusText:result.statusText,headers})
 }
 return result
}}
