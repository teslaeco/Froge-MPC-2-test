// Static application plus explicit retirement of the former paid provider routes.
type Environment={ASSETS:{fetch:(request:Request)=>Promise<Response>}}
export default {async fetch(request:Request,env:Environment):Promise<Response>{
 const url=new URL(request.url)
 if(url.pathname.startsWith('/api/3d/'))return Response.json({error:'Płatny generator został usunięty. Użyj Codexa lub dodatku Blender z lokalnym AI.'},{status:410,headers:{'Cache-Control':'no-store'}})
 const result=await env.ASSETS.fetch(request)
 if(result.status===404&&request.method==='GET'&&request.headers.get('accept')?.includes('text/html'))return env.ASSETS.fetch(new Request(new URL('/index.html',url),request))
 return result
}}
