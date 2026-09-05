import { z } from 'zod'
const amount = z.number().finite().min(0).max(1000000)
export const productSchema = z.object({
  id: z.string().uuid(), title: z.string().trim().min(1).max(160),
  description: z.string().max(5000), prompt: z.string().max(2000),
  kind: z.enum(['figurine', 'part', 'digital', 'other']),
  material: z.string().max(100), variant: z.string().max(100),
  currency: z.enum(['PLN', 'EUR', 'USD']), price: amount, production: amount,
  shipping: amount, packaging: amount, feePercent: z.number().min(0).max(99),
  donation: amount, nonprofit: z.boolean(), supplier: z.string().max(200),
  leadDays: z.number().int().min(0).max(365),
  status: z.enum(['draft', 'review', 'archived']),
  modelFile: z.string().regex(/^[a-f0-9-]{36}\.(glb|json)$/).nullable(),
}).strict()
export type Product = z.infer<typeof productSchema>
export type SavedProduct = Product & { revision: number; updated: string }
export const newProduct = (): Product => ({ id: crypto.randomUUID(), title:'', description:'', prompt:'', kind:'figurine', material:'', variant:'Standard', currency:'PLN', price:0, production:0, shipping:0, packaging:0, feePercent:0, donation:0, nonprofit:false, supplier:'', leadDays:0, status:'draft', modelFile:null })
export function estimate(p: Product) {
  const fees = p.price * p.feePercent / 100
  const costs = p.production + p.shipping + p.packaging + p.donation + fees
  return { fees, costs, balance: p.price - costs, margin: p.price ? (p.price-costs)/p.price*100 : null }
}
export function readiness(p: Product) {
  return [!p.description.trim() && 'Uzupełnij opis dla klienta.', !p.modelFile && 'Dołącz gotowy model 3D.',
    p.kind!=='digital' && !p.material.trim() && 'Wpisz materiał wykonania.',
    p.kind!=='digital' && !p.supplier.trim() && 'Ustal wykonawcę i koszt produkcji.',
    p.kind!=='digital' && !p.leadDays && 'Ustal czas wykonania.',
    !p.nonprofit && p.price===0 && 'Ustal cenę sprzedaży.',
  ].filter(Boolean) as string[]
}
const html = (s:string) => s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!))
// Quote CSV cells and neutralize spreadsheet formula prefixes in user-authored fields.
const cell=(v:string|number)=>'"'+String(v).replace(/^[\s]*[=+@-]/,m=>"'"+m).replace(/"/g,'""')+'"'
export function shopifyCsv(products: Product[]) {
  const headers=['Title','URL handle','Description','Type','Tags','Published on online store','Status','SKU','Option1 name','Option1 value','Price','Requires shipping','Fulfillment service']
  const rows=products.map(p=>[p.title,`froge-${p.id}`,`<p>${html(p.description).replace(/\n/g,'<br>')}</p>`,p.kind,p.nonprofit?'froge,nonprofit':'froge','false','draft',`FROGE-${p.id}`,'Wariant',p.variant||'Standard',p.price.toFixed(2),p.kind==='digital'?'false':'true','manual'])
  return '\uFEFF'+[headers,...rows].map(row=>row.map(cell).join(',')).join('\r\n')
}
export function supplierBrief(p:Product) {
  return `ZAPYTANIE O WYCENĘ — NIE WYSŁANO\n\nProdukt: ${p.title}\nOpis: ${p.description}\nMateriał: ${p.material||'Do ustalenia'}\nWariant: ${p.variant}\nPlanowany wykonawca: ${p.supplier||'Do ustalenia'}\nOczekiwany czas wykonania: ${p.leadDays||'Do ustalenia'} dni\n\nProszę o wycenę prototypu i produkcji, minimalną liczbę sztuk, tolerancje, wykończenie, pakowanie oraz dostępne kraje i koszt wysyłki bezpośrednio do klienta. Proszę potwierdzić przydatność modelu do wykonania i wymagane poprawki.\nModel należy dołączyć oddzielnie.\n\nSpecyfikacja projektowa: ${p.prompt||'Do ustalenia'}`
}
export function tiktokBrief(p:Product) {
  return `SZKIC OFERTY TIKTOK SHOP — NIE OPUBLIKOWANO\n\n${p.title}\n\n${p.description}\n\nWariant: ${p.variant}\nMateriał: ${p.material||'Do ustalenia'}\nCena: ${p.price.toFixed(2)} ${p.currency}\nCzas wykonania: ${p.leadDays||'Do ustalenia'} dni\n\nDo ustalenia przed publikacją: kategoria, zdjęcia gotowego produktu, dostępność, dostawa i zwroty. Sprawdź dopuszczenie produktu i kraju sprzedawcy w TikTok Shop. To dokument roboczy, nie plik importu TikTok.`
}
