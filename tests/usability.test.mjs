import {toggleSource,uploadSourceFiles} from '../design/prototype/analysis-view.js';
import {applySourceAvailability,countrySourceCount,regionalSourceSummary} from '../design/prototype/report-state.js';
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {AIClient} from '../integrations/javascript/ai-client.mjs';
import {storedProfile} from '../design/prototype/profile-view.js';
import {defaultView} from '../integrations/javascript/evidence-model.mjs';
import {methodologyPage,assemblyPanel} from '../design/prototype/methodology-view.js';

test('method library displays the actual task assembly without adding a universal request contract',()=>{
 const method=JSON.parse(readFileSync(new URL('../integrations/fixtures/methodology.json',import.meta.url),'utf8'));
 const assembly=method.assemblies.find(a=>a.id==='operation:translate');
 assembly.instruction_paths=assembly.instruction_paths.filter(path=>!path.endsWith('/00-request-contract.md'));
 const html=methodologyPage(method),translation=html.split('<h3>Translate documents</h3>')[1].split('</article>')[0];
 assert.match(translation,/operations\/translate.md/);
 assert.doesNotMatch(translation,/00-request-contract/);
 assert.doesNotMatch(html,/All tasks also include|Rules shared by every model request/);
 assert.match(assemblyPanel(method),/standalone transcription prompt/);
});

test('conditional commitments stay qualified even when targets are not visible columns',()=>{
 const p=JSON.parse(readFileSync(new URL('../integrations/fixtures/report-experience.json',import.meta.url),'utf8'));
 const before=structuredClone(p),v=defaultView(p);v.columns=['statement','sources'];
 const html=storedProfile({profile:p,selection:{},history:[]},'commitments',v);
 assert.match(html,/class="qualification">Subject to international financing/);
 // A conditional classification with no free-text condition is still visible.
 p.extraction.records[0].targets[0].condition_text=null;
 assert.match(storedProfile({profile:p,selection:{},history:[]},'commitments',v),/Explicitly conditional target/);
 p.extraction.records[0].targets[0].condition_text=before.extraction.records[0].targets[0].condition_text;
 assert.deepEqual(p,before);
});

test('a prepared request survives module reload as a draft and never saves credentials',async t=>{
 const old=Object.getOwnPropertyDescriptor(globalThis,'localStorage'),storage=new Map();
 Object.defineProperty(globalThis,'localStorage',{configurable:true,value:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)}});
 t.after(()=>old?Object.defineProperty(globalThis,'localStorage',old):delete globalThis.localStorage);
 const module=await import('../design/prototype/report-state.js?draft-save');
 const d={task:'brief',document_ids:['doc-1'],requested_fields:['answer'],filters:{hazards:['flood']},groups:[],uploads:[],question:'Which targets need finance?',model:{route:'openai_api',model:'example',effort:'high',api_key:'never-store'},credentials:'never-store'};
 const saved=module.saveRequestDraft(d,'Finance brief');assert.equal(saved.persisted,true);
 d.document_ids.push('doc-2');
 const reloaded=await import('../design/prototype/report-state.js?draft-reload');
 assert.deepEqual(reloaded.requestDrafts()[0].draft.document_ids,['doc-1']);
 assert.equal(reloaded.requestDrafts()[0].draft.question,d.question);
 assert.ok(![...storage.values()].join('').includes('never-store'));
 assert.ok(!reloaded.requestDrafts()[0].result);
 reloaded.saveRequestDraft(d,'Revised finance brief',saved.item.id);assert.equal(reloaded.requestDrafts().length,1);
 localStorage.setItem=()=>{throw Error('Quota exceeded');};
 assert.equal(reloaded.saveRequestDraft(d,'Tab-only draft').persisted,false);
 assert.equal(reloaded.requestDrafts().length,2);
});

test('expired read sessions recover once; model execution is never replayed',async()=>{
 const calls=[];
 const client=new AIClient(async(path,options)=>{
  calls.push([path,options.method]);
  if(path.endsWith('/session'))return {ok:true,json:async()=>({csrf:'renewed'})};
  const n=calls.filter(([p])=>p===path).length;
  return {ok:n>1,json:async()=>n>1?{runs:[]}:{error:{code:'session_expired',message:'Reconnect'}}};
 });
 assert.deepEqual(await client.request('/analyses'),{runs:[]});assert.equal(client.csrf,'renewed');
 assert.deepEqual(calls.map(([p])=>p),['/api/ai/analyses','/api/ai/session','/api/ai/analyses']);
 calls.length=0;
 await assert.rejects(client.request('/analyses',{task:'brief'}),/Reconnect/);
 assert.equal(calls.length,1);assert.equal(calls[0][1],'POST');
});

test('simultaneous page readers share one session initialization',async()=>{
 let n=0;const client=new AIClient(async()=>{n++;await new Promise(resolve=>setImmediate(resolve));return {ok:true,json:async()=>({csrf:'one'})};});
 await Promise.all([client.session(),client.session(),client.session()]);assert.equal(n,1);assert.equal(client.csrf,'one');
});

test('reopened requests keep document choices after clearing their last selection',()=>{
 const draft={document_ids:['first']},documents=[{id:'first',country_code:'ALB'},{id:'second',country_code:'ALB'}];
 toggleSource(draft,'first',false,documents);
 assert.deepEqual(draft.document_ids,[]);
 assert.deepEqual(draft.sourceCountries,['ALB']);
 toggleSource(draft,'second',true,documents);
 assert.deepEqual(draft.document_ids,['second']);
 assert.deepEqual(draft.sourceCountries,['ALB']);
});

test('local availability separates bundled registry metadata from installed originals',()=>{
 const region={countries:[{code:'ALB',document_count:3,local_profile_id:'saved'}],documents:[{id:'a',country_code:'ALB'},{id:'b',country_code:'ALB'},{id:'c',country_code:'ALB'}]};
 applySourceAvailability(region,{documents:[{document_id:'a',status:'available',available:true},{document_id:'b',status:'missing',available:false},{document_id:'c',status:'changed',available:false}]});
 assert.equal(region.countries[0].document_count,1);assert.equal(region.countries[0].registered_document_count,3);assert.equal(region.countries[0].local_profile_id,'saved');
 assert.deepEqual(region.documents.map(d=>d.local_available),[true,false,false]);
 applySourceAvailability(region,null);assert.equal(region.countries[0].document_count,null);assert.ok(region.documents.every(d=>d.local_status==='unknown'));
});

test('failed inventory checks show unknown availability, retain registry counts and recover without claiming missing originals',()=>{
 const region={countries:[{code:'ALB',document_count:2}],documents:[{id:'a',country_code:'ALB'},{id:'b',country_code:'ALB'}]};
 applySourceAvailability(region,null);
 assert.equal(region.countries[0].document_count,null);
 assert.equal(countrySourceCount(region.countries[0]),'2 registered · availability unknown');
 assert.match(regionalSourceSummary(region),/2 registered documents.*could not be checked/);
 assert.doesNotMatch(regionalSourceSummary(region),/0 available|0 of|missing/);
 assert.ok(region.documents.every(d=>d.local_available===false),'Unverified originals cannot be selected for generation');
 applySourceAvailability(region,{documents:region.documents.map(d=>({document_id:d.id,status:'available',available:true}))});
 assert.equal(countrySourceCount(region.countries[0]),'2 documents');assert.match(regionalSourceSummary(region),/2 available of 2/);
 applySourceAvailability(region,{documents:region.documents.map(d=>({document_id:d.id,status:'missing',available:false}))});
 assert.equal(region.countries[0].document_count,0);assert.match(regionalSourceSummary(region),/0 available of 2/);
});

test('a partly successful upload batch refreshes its registered documents after a later failure',async()=>{
 const registered=[],events=[],files=[{name:'first.pdf',size:20},{name:'second.pdf',size:30}];
 await assert.rejects(uploadSourceFiles(files,{readFile:async file=>file.name,register:async file=>{if(file===files[1])throw Error('Invalid second PDF');return {id:'first'};},onRegistered:item=>registered.push(item),refresh:async()=>events.push('refreshed')}),/Invalid second PDF/);
 assert.deepEqual(registered,[{id:'first'}]);assert.deepEqual(events,['refreshed']);
 let called=false;await assert.rejects(uploadSourceFiles([{name:'too-large.pdf',size:25000001}],{readFile:()=>{called=true;}}),/25 MB/);assert.equal(called,false);
});
