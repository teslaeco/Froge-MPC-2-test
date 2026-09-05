export async function commerceRequest(path:string,options?:RequestInit){
 const result=await fetch('/api/commerce/'+path,options)
 if(!result.headers.get('content-type')?.includes('application/json'))throw new Error('Nie można otworzyć katalogu. Zaloguj się ponownie i spróbuj jeszcze raz.')
 const data=await result.json();if(!result.ok)throw new Error(data.error||'Operacja nie powiodła się.');return data
}
