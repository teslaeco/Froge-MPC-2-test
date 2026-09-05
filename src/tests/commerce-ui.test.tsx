import { afterEach,it,expect,vi } from 'vitest'
import { cleanup,render,screen,fireEvent,waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { CommerceHub } from '../commerce/CommerceHub'
afterEach(()=>{cleanup();vi.unstubAllGlobals()})
it('preserves product fields when remote saving fails',async()=>{
 const remote=vi.fn().mockResolvedValueOnce(Response.json({products:[]})).mockResolvedValueOnce(Response.json({error:'Storage unavailable'},{status:503}));vi.stubGlobal('fetch',remote)
 render(<MemoryRouter><CommerceHub/></MemoryRouter>)
 await screen.findByText('Zacznij od jednego pomysłu')
 fireEvent.change(screen.getByLabelText('Nazwa produktu'),{target:{value:'Figurka dębu'}})
 fireEvent.click(screen.getByRole('button',{name:'Zapisz produkt'}))
 await screen.findByText('Storage unavailable',{exact:false})
 expect((screen.getByLabelText('Nazwa produktu') as HTMLInputElement).value).toBe('Figurka dębu')
 expect(screen.getByText('Niezapisane zmiany')).toBeTruthy()
})
it('uses real saved response and retains all channels as unconnected',async()=>{
 vi.stubGlobal('fetch',vi.fn(async(_url:string,options?:RequestInit)=>options?.method==='PUT'?Response.json({product:{...JSON.parse(options.body as string).product,revision:1,updated:'2026-09-06'}}):Response.json({products:[]})))
 render(<MemoryRouter><CommerceHub/></MemoryRouter>)
 await screen.findByText('Zacznij od jednego pomysłu')
 fireEvent.change(screen.getByLabelText('Nazwa produktu'),{target:{value:'Moja figurka'}})
 fireEvent.click(screen.getByRole('button',{name:'Zapisz produkt'}))
 await waitFor(()=>expect(screen.getByText('Produkt zapisany w Twoim katalogu. Oferta pozostaje nieopublikowana.')).toBeTruthy())
 expect(screen.getAllByText('Niepołączony')).toHaveLength(2)
 expect(screen.getByText('Serwer niepołączony')).toBeTruthy()
})
