import {defaultView,validateView} from '../../integrations/javascript/evidence-model.mjs';
const KEY='policytracker.presentation.v1';
let memory, storageOK=true;
const positions=new Map();
function read(){if(memory)return memory;try{memory=JSON.parse(localStorage.getItem(KEY)||'null');}catch{storageOK=false;}if(!memory||memory.schemaVersion!==1||!memory.active||typeof memory.active!=='object'||Array.isArray(memory.active)||!Array.isArray(memory.named))memory={schemaVersion:1,active:{},named:[]};memory.named=memory.named.filter(v=>v&&typeof v.name==='string'&&v.view&&typeof v.view==='object');return memory;}
function write(){try{localStorage.setItem(KEY,JSON.stringify(read()));storageOK=true;}catch{storageOK=false;}return storageOK;}
export function viewKey(p){return `${p.synthetic?'synthetic':'country'}:${p.country_code}:${p.id}`;}
export function getView(p){const saved=read().active[viewKey(p)];if(saved&&!validateView(p,saved).length)return saved;return defaultView(p);}
export function setView(p,view){read().active[viewKey(p)]=structuredClone(view);return write();}
export function storageNotice(){read();return storageOK?'Preferences are saved on this browser. Shared defaults and evidence are unchanged.':'Browser storage is unavailable. Preferences last for this tab only.';}
export function savedViews(p){return read().named.filter(v=>v.country===p.country_code&&v.synthetic===!!p.synthetic&&v.reportType===(p.report_type||'country'));}
export function saveNamed(p,view,name){name=name.trim();if(!name)throw Error('Enter a name for this view.');const item={country:p.country_code,synthetic:!!p.synthetic,reportType:p.report_type||'country',name,view:structuredClone({...view,name})};const list=read().named;const index=list.findIndex(v=>v.country===item.country&&v.synthetic===item.synthetic&&v.reportType===item.reportType&&v.name===name);if(index>=0)list[index]=item;else list.push(item);return write();}
export function applyNamed(p,item){const errors=validateView(p,item.view);if(errors.length)throw Error(errors.join(' '));const view={...structuredClone(item.view),profileId:p.id,codebook:defaultView(p).codebook};setView(p,view);return view;}
export function rememberPosition(key){if(typeof window!=='undefined')positions.set(key,window.scrollY);}
export function restorePosition(key){if(typeof window!=='undefined')window.scrollTo(0,positions.get(key)||0);}
export function restoreFocus(main,elementId,sourceId){
 const doc=main.ownerDocument;
 if(doc.activeElement!==doc.body)return;
 const target=sourceId?main.querySelector(`[data-select-doc="${CSS.escape(sourceId)}"]`):(elementId?doc.getElementById(elementId):null);
 target?.focus({preventScroll:true});
}

// The registry travels with the code; original PDFs do not. Only a server check
// can establish which registered documents this workspace can actually read.
export function applySourceAvailability(region,snapshot){
 const available=new Map((snapshot?.documents||[]).map(d=>[d.document_id,d]));
 const knownStatuses=['available','missing','changed','invalid','unreadable'];
 for(const doc of region.documents){const checked=available.get(doc.id);doc.local_status=knownStatuses.includes(checked?.status)?checked.status:'unknown';doc.local_available=checked?.available===true&&doc.local_status==='available';}
 region.source_availability_known=Array.isArray(snapshot?.documents)&&region.documents.every(d=>d.local_status!=='unknown');
 for(const country of region.countries){const registered=region.documents.filter(d=>d.country_code===country.code);country.registered_document_count=registered.length;country.document_count=registered.some(d=>d.local_status==='unknown')?null:registered.filter(d=>d.local_available).length;}
}

export function countrySourceCount(country){return country.document_count===null?`${country.registered_document_count} registered · availability unknown`:`${country.document_count} ${country.document_count===1?'document':'documents'}`;}
export function regionalSourceSummary(region){
 if(!region.source_availability_known)return `${region.documents.length} registered documents. Local source availability could not be checked.`;
 return `${region.countries.filter(c=>c.document_count).length} of ${region.countries.length} countries have source documents available locally. ${region.documents.filter(d=>d.local_available).length} available of ${region.documents.length} registered documents.`;
}

// Current country selections and exact historical reads have different identities.
// Visiting history must never replace the version used by regional summaries.
export function createProfileCache(){
 const current=new Map(),versions=new Map(),metadata=new Map(),key=(country,version)=>JSON.stringify([country,version]);
 const get=(country,version=null)=>{
  const saved=version?versions.get(key(country,version)):current.get(country),latest=metadata.get(country);
  if(!saved||saved.error||!latest)return saved;
  // An exact-version response can reveal a different selected profile without
  // supplying its content. Refetch that selection instead of showing old data.
  if(!version&&(saved.profile?.id||null)!==(latest.selection?.profile_id||null))return undefined;
  const entry=latest.history?.find(item=>item.id===saved.profile?.id);
  return {...saved,...latest,profile:saved.profile?{...saved.profile,published:entry?!!entry.published:saved.profile.published}:saved.profile};
 };
 return {
  get,
  set(country,data,version=null){
   if(version&&!data.error&&data.profile?.id!==version)throw Error('The requested profile version is unavailable. No other version has been substituted.');
   const fresh=(data.selection?.revision??0)>=(metadata.get(country)?.selection?.revision??0);
   if(!version&&!fresh&&!data.error)return;
   (version?versions:current).set(version?key(country,version):country,data);
   // History/publication can change without changing the selected version's
   // revision. Keep the latest fetched metadata, including historical reads.
   if(!data.error&&fresh)metadata.set(country,{selection:data.selection,history:data.history});
  },
  values(){return [...current.keys()].map(country=>get(country)).filter(Boolean);}
 };
}

// Prepared requests are browser-local drafts, never completed analysis results.
const DRAFT_KEY='policytracker.request-drafts.v1';
let drafts;
export function requestDrafts(){
 if(drafts)return structuredClone(drafts);
 try{const data=JSON.parse(localStorage.getItem(DRAFT_KEY)||'[]');drafts=Array.isArray(data)?data.filter(x=>x&&typeof x.id==='string'&&typeof x.name==='string'&&x.draft&&Array.isArray(x.draft.document_ids)):[];}catch{drafts=[];}
 return structuredClone(drafts);
}
export function saveRequestDraft(draft,name,id){
 requestDrafts();name=name.trim();if(!name)throw Error('Give this request a name so you can find it later.');
 // Explicitly select request fields. Never persist connection status or credentials.
 const keys=['task','document_ids','requested_fields','filters','comparison_mode','groups','include_analyst_proposals','question','instructions','uploads'];
 const clean=Object.fromEntries(keys.map(k=>[k,structuredClone(draft[k])]));
 clean.model=Object.fromEntries(['route','model','effort','max_output_tokens'].filter(k=>draft.model?.[k]!==undefined).map(k=>[k,draft.model[k]]));
 const item={id:id||crypto.randomUUID(),name:name.slice(0,100),saved_at:new Date().toISOString(),draft:clean};
 const index=drafts.findIndex(d=>d.id===item.id);if(index<0)drafts.unshift(item);else drafts[index]=item;
 let persisted=true;try{localStorage.setItem(DRAFT_KEY,JSON.stringify(drafts));}catch{persisted=false;}
 return {item:structuredClone(item),persisted};
}
