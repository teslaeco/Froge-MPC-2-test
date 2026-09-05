import { describe, it, expect, vi } from 'vitest'
import { newProduct, estimate, shopifyCsv, productSchema } from '../commerce/domain'
import { commerceApi, type CommerceEnv } from '../commerce/server'
const product=()=>({...newProduct(),title:'Smok, "zielony"',description:'<script>alert(1)</script>\nDetal',price:100,production:30,shipping:10,packaging:5,feePercent:10,donation:5})
const request=(body:unknown,headers:Record<string,string>={})=>new Request('https://froge.test/api/commerce/products',{method:'PUT',headers:{origin:'https://froge.test','Content-Type':'application/json','oai-authenticated-user-id':'owner-a',...headers},body:JSON.stringify(body)})
describe('Commerce calculations and draft exports',()=>{
 it('includes delivery, packaging, percentage fees and social allocation',()=>{expect(estimate(product())).toEqual({costs:60,fees:10,balance:40,margin:40})})
 it('does not claim margin on a free nonprofit item',()=>expect(estimate({...product(),price:0,nonprofit:true}).margin).toBeNull())
 it('exports drafts only, quotes CSV, escapes HTML and has stable unique handles',()=>{const p=product(),csv=shopifyCsv([p]);expect(csv).toContain('Smok, ""zielony""');expect(csv).toContain('&lt;script&gt;');expect(csv).toContain('"false","draft"');expect(csv).toContain(`froge-${p.id}`)})
 it('neutralizes spreadsheet formulas and refuses invalid prices',()=>{expect(shopifyCsv([{...product(),title:'=HYPERLINK("x")'}])).toContain("'=HYPERLINK");expect(productSchema.safeParse({...product(),price:-1}).success).toBe(false)})
})
describe('Commerce API boundaries',()=>{
 it('rejects unauthenticated catalog access',async()=>expect((await commerceApi(new Request('https://froge.test/api/commerce/products'),{})).status).toBe(401))
 it('rejects cross-origin writes before database access',async()=>expect((await commerceApi(request({}, {origin:'https://evil.test'}),{})).status).toBe(403))
 it('reports unavailable storage without claiming a successful save',async()=>expect((await commerceApi(request({product:product(),revision:0}),{})).status).toBe(503))
 it('limits declared payload size before reading',async()=>{const env={DB:{prepare:vi.fn()}} as unknown as CommerceEnv;expect((await commerceApi(request({}, {'content-length':'999999999'}),env)).status).toBe(413);expect(env.DB!.prepare).not.toHaveBeenCalled()})
 it('binds both authenticated owner and revision for optimistic updates',async()=>{const bind=vi.fn().mockReturnValue({run:async()=>({meta:{changes:0}})}),prepare=vi.fn().mockReturnValue({bind});const p=product();const result=await commerceApi(request({product:p,revision:7}),{DB:{prepare}} as unknown as CommerceEnv);expect(result.status).toBe(409);expect(prepare.mock.calls[0][0]).toContain('owner=? AND revision=?');expect(bind.mock.calls[0].slice(-3)).toEqual([p.id,'owner-a',7])})
 it('reads only the current authenticated owner',async()=>{const bind=vi.fn().mockReturnValue({all:async()=>({results:[]})});await commerceApi(new Request('https://froge.test/api/commerce/products',{headers:{'oai-authenticated-user-id':'owner-a'}}),{DB:{prepare:()=>({bind})}} as unknown as CommerceEnv);expect(bind).toHaveBeenCalledWith('owner-a')})
})
