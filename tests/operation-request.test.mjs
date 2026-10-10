import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {compileRequest,describeRequest} from '../integrations/javascript/operation-request.mjs';
const read=p=>JSON.parse(readFileSync(new URL(p,import.meta.url),'utf8'));
const catalog=read('../integrations/fixtures/operation-tasks.json');
const region=read('../integrations/fixtures/regional-workspace.json');
const kaz=region.documents.filter(d=>d.country_code==='KAZ').map(d=>d.id);
const alb=region.documents.filter(d=>d.country_code==='ALB');
const base=()=>({task:'extract',document_ids:kaz,requested_fields:['targets','finance'],filters:{hazards:['flood']},model:{model:'gpt-6-astra',effort:'xhigh',route:'codex_chatgpt'},instructions:'Retain financing conditions.'});
test('partly overlapping editions cannot oppose each other across groups',()=>{
 const r=structuredClone(region);
 const chosen=r.documents.slice(0,3);
 chosen[0].edition_id='same';chosen[1].edition_id='different';chosen[2].edition_id='same';
 const d={...base(),task:'compare',comparison_mode:'custom',document_ids:chosen.map(x=>x.id),groups:[{label:'A',document_ids:chosen.slice(0,2).map(x=>x.id)},{label:'B',document_ids:[chosen[2].id]}]};
 assert.throws(()=>compileRequest(d,catalog,r),/share a policy edition/);
});
test('customizations survive in the request and change its output requirements',()=>{
 const d=base(),r=compileRequest(d,catalog,region);assert.deepEqual(r.filters.hazards,['flood']);assert.equal(r.instructions,d.instructions);assert.equal(r.model.effort,'xhigh');assert.equal(r.kind,'ad_hoc');
 const s=describeRequest(r,catalog);assert.equal(s.effects.length,2);assert.ok(s.effects.some(x=>x.includes('financing')));
 d.requested_fields=['indicators'];const changed=compileRequest(d,catalog,region);assert.notDeepEqual(changed.requested_fields,r.requested_fields);assert.ok(describeRequest(changed,catalog).effects[0].includes('indicators'));
});
test('unknown sources and empty field selections are rejected',()=>{
 assert.throws(()=>compileRequest({...base(),document_ids:['invented']},catalog,region),/unknown document/);
 assert.throws(()=>compileRequest({...base(),requested_fields:[]},catalog,region),/at least one output/);
});

test('known registry entries cannot run when their originals are missing or changed locally',()=>{
 const r=structuredClone(region),d=base();r.documents.find(doc=>doc.id===d.document_ids[0]).local_available=false;
 assert.throws(()=>compileRequest(d,catalog,r),/original is unavailable/);
 r.documents.find(doc=>doc.id===d.document_ids[0]).local_available=true;
 assert.equal(compileRequest(d,catalog,r).task,'extract');
 r.documents.find(doc=>doc.id===d.document_ids[0]).local_available=false;
 r.documents.find(doc=>doc.id===d.document_ids[0]).local_status='unknown';
 assert.throws(()=>compileRequest(d,catalog,r),/availability has not been checked/);
});
test('country comparison rejects one country and supports three groups',()=>{
 const d={...base(),task:'compare',comparison_mode:'countries'};assert.throws(()=>compileRequest(d,catalog,region),/at least two/);
 d.document_ids=[...kaz,alb[0].id,region.documents.find(d=>d.country_code==='ARM').id];assert.equal(compileRequest(d,catalog,region).source_groups.length,3);
});
test('custom comparison requires complete, exclusive group assignments',()=>{
 const d={...base(),task:'compare',comparison_mode:'custom',groups:[{label:'A',document_ids:[kaz[0]]},{label:'B',document_ids:[kaz[0]]}]};
 assert.throws(()=>compileRequest(d,catalog,region),/exactly one/);d.groups[1].document_ids=[kaz[1]];assert.equal(compileRequest(d,catalog,region).source_groups.length,2);
});
test('NDC-NAP comparison rejects two NDC groups',()=>{
 const d={...base(),task:'compare',comparison_mode:'ndc_nap',groups:[{label:'NDC',document_ids:[kaz[0]]},{label:'NAP',document_ids:[kaz[1]]}]};assert.throws(()=>compileRequest(d,catalog,region),/at least two/);
});
test('brief requires a policy question and ignores stale gap proposals',()=>{
 const d={...base(),task:'brief',include_analyst_proposals:true};assert.throws(()=>compileRequest(d,catalog,region),/policy question/);d.question='Which commitments depend on external finance?';assert.equal(compileRequest(d,catalog,region).include_analyst_proposals,false);
});
test('uploads remain pending, do not invent source IDs and cannot appear as completed work',()=>{
 const r=compileRequest({...base(),uploads:['ministry.pdf']},catalog,region);assert.equal(r.uploads[0].state,'local_pending');assert.equal(r.execution_state,'not_run');assert.deepEqual(r.source_groups[0].document_ids,kaz);
});

test('one document works for extraction; document comparison needs two and accepts same-country files',()=>{
 const d={...base(),document_ids:[kaz[0]]};assert.equal(compileRequest(d,catalog,region).source_groups[0].document_ids.length,1);
 assert.throws(()=>compileRequest({...d,task:'compare',comparison_mode:'documents'},catalog,region),/at least 2/);
 assert.equal(compileRequest({...base(),task:'compare',comparison_mode:'documents'},catalog,region).source_groups.length,2);
});

test('NDC-NAP mode groups automatically; revision rejects different instruments and excess groups',()=>{
 const r=compileRequest({...base(),document_ids:alb.map(d=>d.id),task:'compare',comparison_mode:'ndc_nap'},catalog,region);
 assert.equal(r.source_groups.length,2);assert.equal(r.source_groups[0].label,'NDC');assert.ok(r.source_groups[1].document_ids.length);
 const ndc=alb.find(d=>d.declared_type==='NDC'),nap=alb.find(d=>d.declared_type==='NAP');
 assert.throws(()=>compileRequest({...base(),document_ids:[ndc.id,nap.id],task:'compare',comparison_mode:'revision',groups:[{label:'Earlier',document_ids:[ndc.id]},{label:'Later',document_ids:[nap.id]}]},catalog,region),/same instrument/);
});

test('full translation clears thematic filters and stale questions; preserves all selected documents',()=>{
 const r=compileRequest({...base(),task:'translate',requested_fields:[],question:'Old briefing question'},catalog,region);
 assert.equal(r.output.artifact,'bilingual_documents');assert.equal(r.source_groups[0].document_ids.length,2);assert.equal(r.question,'');assert.ok(Object.values(r.filters).every(v=>v.length===0));assert.equal(describeRequest(r,catalog).effects.length,3);
});

test('topic and sector must agree; supported topic changes saved scope',()=>{
 const d={...base(),filters:{domain_ids:['energy'],topic_ids:['CLM-01']}};assert.throws(()=>compileRequest(d,catalog,region),/outside/);
 d.filters.domain_ids=['climate'];assert.deepEqual(compileRequest(d,catalog,region).filters.topic_ids,['CLM-01']);
});

test('multiple domains, topics, hazards and functions survive request compilation',()=>{
 const filters={domain_ids:['agriculture','water','energy'],topic_ids:['AGR-01','ENE-01'],
   hazards:['flood','drought'],risk_functions:['early_warning_preparedness','coping_continuity']};
 const request=compileRequest({...base(),filters},catalog,region);
 assert.deepEqual(request.filters,filters);
 assert.deepEqual(request.source_groups[0].document_ids,kaz);
 assert.equal(request.schema_version,'2.0.0');
});


test('omitted option list uses configured defaults while explicit empty remains invalid',()=>{
 const draft=base();delete draft.requested_fields;
 assert.deepEqual(compileRequest(draft,catalog,region).requested_fields,catalog.tasks.find(t=>t.id==='extract').options.filter(o=>o.default).map(o=>o.id));
 assert.throws(()=>compileRequest({...draft,requested_fields:[]},catalog,region),/at least one/);
});
