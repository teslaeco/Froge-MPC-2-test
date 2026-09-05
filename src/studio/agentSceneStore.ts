import { sceneSchema,type ModelScene } from './scene'
type State={revision:number;request:{id:string;prompt:string}|null;scene:ModelScene|null;status:'idle'|'waiting'|'ready';note:string}
let state:State={revision:1,request:null,scene:null,status:'idle',note:''}
const listeners=new Set<()=>void>()
export const getAgentScene=()=>state
export function invalidateAgentRequest(){state={...state,revision:state.revision+1,request:null,scene:null,status:'idle',note:''};emit()}
export function subscribeAgentScene(fn:()=>void){listeners.add(fn);return()=>{listeners.delete(fn)}}
function emit(){listeners.forEach(fn=>fn())}
export function requestAgentModel(prompt:string){if(!prompt.trim()||prompt.length>2000)throw new Error('Wpisz opis od 1 do 2000 znaków.');state={...state,revision:state.revision+1,request:{id:crypto.randomUUID(),prompt:prompt.trim()},status:'waiting',note:'Polecenie przygotowane. Poproś agenta przeglądarki o wykonanie albo skopiuj je do rozmowy z Codexem.'};emit();return state.request}
export function applyAgentScene(value:unknown,expectedRevision:number,requestId:string|null){if(state.revision!==expectedRevision||(state.request?.id??null)!==requestId)return{state:'CONFLICT',revision:state.revision};const parsed=sceneSchema.safeParse(value);if(!parsed.success)return{state:'FAIL',errors:parsed.error.issues.map(x=>x.message)};state={...state,scene:parsed.data,revision:state.revision+1,status:'ready',note:'Model dostarczony. Podgląd i eksport korzystają z tej samej geometrii.'};emit();return{state:'PASS',revision:state.revision}}
