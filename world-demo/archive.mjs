const DB_NAME='forge-world-v1';
let dbPromise;
function openDB(){return dbPromise??=new Promise((resolve,reject)=>{const q=indexedDB.open(DB_NAME,1);q.onupgradeneeded=()=>{q.result.createObjectStore('assets',{keyPath:'id'});q.result.createObjectStore('world',{keyPath:'id'});};q.onsuccess=()=>resolve(q.result);q.onerror=()=>reject(q.error);});}
async function transaction(store,mode,fn){const db=await openDB();return new Promise((resolve,reject)=>{const t=db.transaction(store,mode);let result;const q=fn(t.objectStore(store));q.onsuccess=()=>{result=q.result;};t.oncomplete=()=>resolve(result);t.onerror=()=>reject(t.error);t.onabort=()=>reject(t.error??Error('Zapis przerwany.'));});}
export async function saveAsset(asset){if(!asset.id||!asset.blob)throw Error('Niekompletne archiwum modelu.');return transaction('assets','readwrite',s=>s.add(asset));}
export const listAssets=()=>transaction('assets','readonly',s=>s.getAll());
export const getAsset=id=>transaction('assets','readonly',s=>s.get(id));
export const saveWorld=data=>transaction('world','readwrite',s=>s.put({id:'current',...data,updatedAt:new Date().toISOString()}));
export const loadWorld=()=>transaction('world','readonly',s=>s.get('current'));
export async function sha256(blob){const data=blob instanceof Blob?await blob.arrayBuffer():blob;return [...new Uint8Array(await crypto.subtle.digest('SHA-256',data))].map(x=>x.toString(16).padStart(2,'0')).join('');}
export async function durableStorage(){return navigator.storage?.persist?await navigator.storage.persist():false;}
