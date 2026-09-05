import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { estimate, newProduct, productSchema, readiness, shopifyCsv, supplierBrief, tiktokBrief, type Product, type SavedProduct } from './domain'
import './commerce.css'
import { commerceRequest as api } from './client'

type Section='catalog'|'offers'|'channels'
const kinds={figurine:'Figurka 3D',part:'Część użytkowa',digital:'Plik cyfrowy',other:'Inny produkt'}
const statuses={draft:'Szkic',review:'Do sprawdzenia',archived:'Archiwum'}
const money=(n:number,c:string)=>new Intl.NumberFormat('pl-PL',{style:'currency',currency:c}).format(n)
function download(name:string,text:string,type='text/plain;charset=utf-8'){
 const url=URL.createObjectURL(new Blob([text],{type})); const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)
}
export function CommerceHub(){
 const [section,setSection]=useState<Section>('catalog'),[products,setProducts]=useState<SavedProduct[]>([])
 const [form,setForm]=useState<Product>(newProduct),[revision,setRevision]=useState(0),[dirty,setDirty]=useState(false)
 const [loading,setLoading]=useState(true),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('')
 const [search,setSearch]=useState(''),[filter,setFilter]=useState('all'),[exportCurrency,setExportCurrency]=useState('PLN')
 const costs=estimate(form),checks=readiness(form)
 const valid=productSchema.safeParse(form).success
 async function load(){setLoading(true);setError('');try{const data=await api('products');setProducts(data.products);const wanted=new URLSearchParams(window.location.search).get('product');if(wanted&&!dirty&&revision===0){const found=data.products.find((p:SavedProduct)=>p.id===wanted);if(found){const {revision:r,updated:_,...product}=found;setForm(product);setRevision(r)}}}catch(e){setError((e as Error).message)}finally{setLoading(false)}}
 useEffect(()=>{void load();const refresh=()=>{void api('products').then(data=>{setProducts(data.products);setNotice('Agent zaktualizował katalog. Otwórz produkt ponownie, aby zobaczyć nową wersję formularza.')}).catch(e=>setError(e.message))};window.addEventListener('froge-catalog-updated',refresh);return()=>window.removeEventListener('froge-catalog-updated',refresh)},[])
 useEffect(()=>{const handler=(event:BeforeUnloadEvent)=>{if(dirty){event.preventDefault();event.returnValue=''}};window.addEventListener('beforeunload',handler);return()=>window.removeEventListener('beforeunload',handler)},[dirty])
 const patch=(change:Partial<Product>)=>{setForm(p=>({...p,...change}));setDirty(true);setNotice('')}
 function choose(product?:SavedProduct){
  if(busy)return
  if(dirty&&!window.confirm('Masz niezapisane zmiany. Odrzucić je i otworzyć inny produkt?'))return
  if(product){const {revision:r,updated:_,...p}=product;setForm(p);setRevision(r)}else{setForm(newProduct());setRevision(0)}
  setDirty(false);setNotice('');setError('');setSection('catalog')
 }
 async function save(event:FormEvent){
  event.preventDefault();if(busy||!valid)return;setBusy(true);setError('');setNotice('')
  try{const data=await api('products',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({product:form,revision})});const p=data.product as SavedProduct;setProducts(old=>[p,...old.filter(x=>x.id!==p.id)]);setRevision(p.revision);setDirty(false);setNotice('Produkt zapisany w Twoim katalogu. Oferta pozostaje nieopublikowana.')}
  catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 async function upload(file?:File){
  if(!file)return
  if(file.size>12*1024*1024){setError('Maksymalny rozmiar modelu to 12 MB.');return}
  if(!/\.(json|glb)$/i.test(file.name)){setError('Wybierz model GLB lub Froge JSON.');return}
  setBusy(true);setError('')
  try{const data=await api('models',{method:'POST',headers:{'Content-Type':file.name.toLowerCase().endsWith('.json')?'application/json':'model/gltf-binary'},body:file});patch({modelFile:data.filename});setNotice('Model przesłany. Zapisz produkt, aby zachować powiązanie.')}
  catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 const visible=products.filter(p=>(filter==='all'?p.status!=='archived':p.status===filter)&&`${p.title} ${p.material}`.toLocaleLowerCase('pl').includes(search.toLocaleLowerCase('pl')))
 const selectedExport=products.filter(p=>p.status!=='archived'&&p.currency===exportCurrency)
 const count=products.filter(p=>p.status!=='archived').length
 return <div className="commerce">
  <header className="commerce-heading"><div><p className="commerce-kicker">FROGE / CENTRUM SPRZEDAŻY</p><h1>Od pomysłu do produktu.</h1><p>Twoje modele, oferty i przygotowanie produkcji w jednym miejscu.</p></div><Link className="commerce-outline" to="/">Otwórz studio 3D ↗</Link></header>
  <nav className="commerce-tabs" aria-label="Panel sprzedaży">{([['catalog','Katalog'],['offers','Oferty i produkcja'],['channels','Kanały sprzedaży']] as const).map(([key,title])=><button key={key} className={section===key?'active':''} onClick={()=>setSection(key)} aria-current={section===key?'page':undefined}>{title}</button>)}</nav>
  <div className="commerce-strip"><span><strong>{count}</strong> {count===1?'produkt w katalogu':'produktów w katalogu'}</span><span>Shopify <b>Niepołączony</b></span><span>TikTok Shop <b>Niepołączony</b></span><span>Blender <b>Serwer niepołączony</b></span></div>
  {error&&<div className="commerce-alert" role="alert">{error} <button onClick={()=>void load()} disabled={loading||busy}>Odśwież katalog</button><p>Odświeżenie listy nie nadpisuje formularza. Przy konflikcie wersji skopiuj swoje zmiany przed ponownym otwarciem produktu.</p></div>}
  {notice&&<p className="commerce-notice" role="status">{notice}</p>}
  {section==='catalog'&&<div className="commerce-workspace">
   <aside className="commerce-panel commerce-list"><div className="commerce-panel-head"><h2>Twoje produkty</h2><button onClick={()=>choose()} disabled={busy} className="commerce-accent">+ Nowy</button></div>
    <label>Szukaj produktu<input type="search" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Nazwa lub materiał" /></label>
    <label>Status<select value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">Bieżące produkty</option><option value="draft">Szkice</option><option value="review">Do sprawdzenia</option><option value="archived">Archiwum</option></select></label>
    {loading?<p role="status">Wczytuję katalog…</p>:!visible.length?<div className="commerce-empty"><span>01</span><h3>{products.length?'Brak pasujących produktów':'Zacznij od jednego pomysłu'}</h3><p>Dodaj figurkę, część lub plik 3D. Zapisany produkt będzie dostępny po ponownym otwarciu platformy.</p></div>:<div className="commerce-product-list">{visible.map(p=><button key={p.id} className={p.id===form.id?'selected':''} onClick={()=>choose(p)} disabled={busy}><span>{kinds[p.kind]} · {statuses[p.status]}</span><strong>{p.title}</strong><small>{p.material||'Materiał do ustalenia'}</small><b>{money(p.price,p.currency)}</b>{p.nonprofit&&<em>Projekt non-profit</em>}</button>)}</div>}
   </aside>
   <form className="commerce-panel commerce-editor" onSubmit={save}><div className="commerce-panel-head"><div><p className="commerce-kicker">KARTA PRODUKTU</p><h2>{form.title||'Nowy produkt'}</h2></div><span className="commerce-tag">{dirty?'Niezapisane zmiany':revision?'Zapisano':'Szkic'}</span></div>
    <fieldset disabled={busy}><div className="commerce-fields"><label className="wide">Nazwa produktu<input required maxLength={160} value={form.title} onChange={e=>patch({title:e.target.value})} placeholder="Np. Figurka smoka na zamówienie" /></label>
     <label>Rodzaj<select value={form.kind} onChange={e=>patch({kind:e.target.value as Product['kind']})}>{Object.entries(kinds).map(([id,title])=><option key={id} value={id}>{title}</option>)}</select></label>
     <label>Status<select value={form.status} onChange={e=>patch({status:e.target.value as Product['status']})}>{Object.entries(statuses).map(([id,title])=><option key={id} value={id}>{title}</option>)}</select></label>
     <label className="wide">Opis dla klienta<textarea rows={4} maxLength={5000} value={form.description} onChange={e=>patch({description:e.target.value})} placeholder="Co klient otrzyma? Opisz wygląd, zastosowanie i personalizację." /></label>
     <label>Materiał<input value={form.material} maxLength={100} onChange={e=>patch({material:e.target.value})} placeholder="Np. żywica, PLA" /></label>
     <label>Wariant<input value={form.variant} maxLength={100} onChange={e=>patch({variant:e.target.value})} placeholder="Np. zielony / 10 cm" /></label>
    </div>
    <details className="commerce-details"><summary>Projekt 3D · opis, wymiary i plik</summary><p>Wymiary i kąty są opcjonalne. Tutaj zapisujesz specyfikację produktu; modelowanie odbywa się w studiu.</p><label>Polecenie modelowania<textarea rows={3} maxLength={2000} value={form.prompt} onChange={e=>patch({prompt:e.target.value})} placeholder="Opisz dowolny obiekt. Wymiary dodaj, jeśli ich potrzebujesz." /></label>
     <label className="commerce-upload">Dołącz gotowy model · GLB lub Froge JSON, do 12 MB<input type="file" accept=".glb,.json" onChange={e=>{void upload(e.target.files?.[0]);e.target.value=''}} /></label>
     {form.modelFile&&<a href={'/api/commerce/models/'+form.modelFile} download>Pobierz przypisany model 3D ↓</a>}
     {form.prompt.trim()&&<button type="button" onClick={()=>download('polecenie-blender.json',JSON.stringify({type:'froge-modeling-request',version:1,prompt:form.prompt},null,2),'application/json')}>Pobierz polecenie do dodatku Blender</button>}
     <p>Plik jest załącznikiem projektu. Przed produkcją wykonawca musi sprawdzić geometrię i możliwość druku.</p>
    </details>
    <h3>Cena i wykonanie</h3><div className="commerce-fields"><label>Waluta<select value={form.currency} onChange={e=>patch({currency:e.target.value as Product['currency']})}><option>PLN</option><option>EUR</option><option>USD</option></select></label>
     {([['price','Cena produktu'],['production','Koszt wykonania'],['shipping','Koszt dostawy'],['packaging','Koszt opakowania'],['donation','Kwota na cel społeczny']] as const).map(([key,title])=><label key={key}>{title} ({form.currency})<input type="number" required min={0} max={1000000} step="0.01" value={form[key]} onChange={e=>patch({[key]:e.target.valueAsNumber})} /></label>)}
     <label>Łączne opłaty od ceny (%)<input type="number" required min={0} max={99} step="0.01" value={form.feePercent} onChange={e=>patch({feePercent:e.target.valueAsNumber})} /></label>
     <label>Czas wykonania (dni)<input type="number" min={0} max={365} step={1} value={form.leadDays} onChange={e=>patch({leadDays:e.target.valueAsNumber})} /></label>
     <label className="wide">Wykonawca / dostawca<input maxLength={200} value={form.supplier} onChange={e=>patch({supplier:e.target.value})} placeholder="Nazwa sprawdzonego wykonawcy" /></label></div>
     <label className="commerce-check"><input type="checkbox" checked={form.nonprofit} onChange={e=>patch({nonprofit:e.target.checked})} />Projekt non-profit</label>
     <p className="commerce-help">Oznaczenie non-profit nie uruchamia darowizn ani nie zmienia ceny. Opłaty wpisujesz na podstawie warunków swoich usług.</p>
    </fieldset>
    <div className="commerce-save"><span>{revision?'Zapis na Twoim koncie':'Produkt nie został jeszcze zapisany'}</span><button className="commerce-accent" disabled={busy||!valid} type="submit">{busy?'Trwa operacja…':'Zapisz produkt'}</button></div>
   </form>
   <aside className="commerce-summary"><div className="commerce-panel"><p className="commerce-kicker">KALKULACJA ROBOCZA</p><h2>Co zostaje z ceny?</h2><div className={'commerce-balance '+(costs.balance<0?'negative':'')}>{Number.isFinite(costs.balance)?money(costs.balance,form.currency):'—'}</div><dl><div><dt>Koszty razem</dt><dd>{Number.isFinite(costs.costs)?money(costs.costs,form.currency):'—'}</dd></div><div><dt>W tym opłaty</dt><dd>{Number.isFinite(costs.fees)?money(costs.fees,form.currency):'—'}</dd></div></dl><p>Saldo przed podatkami, kosztami stałymi i zwrotami. Używaj kwot na tej samej podstawie. Założono, że pokrywasz podany koszt dostawy.</p></div>
    <div className="commerce-panel"><h3>Przed wystawieniem</h3>{checks.length?<ul>{checks.map(c=><li key={c}>{c}</li>)}</ul>:<p>Podstawowe dane są uzupełnione. Sprawdź zdjęcia, prawa do wzoru, dostawę i wymagania kanału.</p>}<button className="commerce-outline" onClick={()=>setSection('offers')}>Przygotuj ofertę →</button></div>
   </aside>
  </div>}
  {section==='offers'&&<div className="commerce-offers"><section className="commerce-panel"><p className="commerce-kicker">01 / SHOPIFY</p><h2>Katalog gotowy do przeniesienia</h2><p>Eksportuj zapisane produkty jako szkice Shopify. Import nie dołącza plików 3D ani nie publikuje ofert.</p><label>Waluta sklepu docelowego<select value={exportCurrency} onChange={e=>setExportCurrency(e.target.value)}><option>PLN</option><option>EUR</option><option>USD</option></select></label><p>{selectedExport.length} produktów w wybranej walucie. CSV nie zawiera oznaczenia waluty: przed importem sprawdź walutę sklepu. Kwoty nie są przeliczane.</p><button className="commerce-accent" disabled={!selectedExport.length} onClick={()=>download('froge-shopify-drafts.csv',shopifyCsv(selectedExport),'text/csv;charset=utf-8')}>Pobierz szkice Shopify CSV ↓</button><a href="https://help.shopify.com/en/manual/products/import-export/import-products" target="_blank" rel="noreferrer">Jak zaimportować produkty</a></section>
   <section className="commerce-panel"><p className="commerce-kicker">02 / TIKTOK SHOP</p><h2>Opis aktualnego produktu</h2><p>{form.title||'Najpierw wybierz lub utwórz produkt w katalogu.'}</p><p>Przygotuj tekst do edycji w kanale TikTok. To szkic roboczy; zdjęcia gotowego produktu i kategorię dodasz przed publikacją.</p><button className="commerce-outline" disabled={!valid} onClick={()=>download('froge-tiktok-oferta.txt',tiktokBrief(form))}>Pobierz opis oferty ↓</button><p className="commerce-help">{dirty?'Uwaga: tekst obejmuje niezapisane zmiany formularza.':'Oferta nie została wysłana do TikTok.'}</p></section>
   <section className="commerce-panel"><p className="commerce-kicker">03 / PRODUKCJA B2B</p><h2>Wycena u wykonawcy</h2><p>Przygotuj zapytanie o prototyp, wykonanie, pakowanie i wysyłkę do klienta. Dane klienta nie są potrzebne do przygotowania tego zapytania.</p><button className="commerce-outline" disabled={!valid} onClick={()=>download('froge-zapytanie-do-wykonawcy.txt',supplierBrief(form))}>Pobierz zapytanie o wycenę ↓</button><p>Zapytanie nie jest automatycznie wysyłane. Załącz gotowy model oddzielnie.</p></section>
  </div>}
  {section==='channels'&&<div className="commerce-offers"><section className="commerce-panel"><p className="commerce-kicker">SHOPIFY</p><h2>Centrum sklepu</h2><span className="commerce-tag">Brak połączenia</span><p>Dostęp agenta do konkretnego sklepu wymaga autoryzacji Shopify. Połączenie Shopify z rozmową nie uruchamia automatycznej synchronizacji tej platformy.</p><a className="commerce-outline" href="https://admin.shopify.com/" target="_blank" rel="noreferrer">Otwórz panel Shopify ↗</a><p>Na razie możesz przenosić szkice przez CSV. Zamówienia, płatności i dostawy obsługuje panel Twojego sklepu.</p></section>
   <section className="commerce-panel"><p className="commerce-kicker">TIKTOK SHOP</p><h2>Sprzedaż przez TikTok</h2><span className="commerce-tag">Brak połączenia</span><p>Oficjalny kanał TikTok w Shopify może synchronizować produkty, zapasy i zamówienia po podłączeniu kwalifikującego się sklepu.</p><p>Sprawdź kraj rejestracji firmy. W dokumentacji sprawdzonej 06.09.2026 Polska i Holandia nie są wymienione wśród krajów obsługiwanych przez kanał TikTok Shop w Shopify.</p><a href="https://help.shopify.com/en/manual/online-sales-channels/social-commerce/tiktok/setup" target="_blank" rel="noreferrer">Wymagania i konfiguracja kanału ↗</a></section>
   <section className="commerce-panel"><p className="commerce-kicker">CODEX + BLENDER</p><h2>Warsztat modeli 3D</h2><span className="commerce-tag">Serwer niepołączony</span><p>Studio obsługuje podgląd i eksport modeli oraz polecenia dla agenta. Dodatek Blender jest gotowy do pobrania; wykonywanie zadań na Oracle wymaga jeszcze konfiguracji.</p><Link className="commerce-outline" to="/">Przejdź do studia ↗</Link><a href="/downloads/froge-blender-addon.zip" download>Pobierz dodatek Blender ↓</a></section>
  </div>}
  <footer className="commerce-footer"><span>FROGE · Studio i sprzedaż</span><Link to="/shop-lab">Laboratorium prototypów</Link><Link to="/contest">Fundament konkursowy</Link></footer>
 </div>
}
