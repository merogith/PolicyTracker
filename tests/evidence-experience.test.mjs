import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {filterRecords,defaultView,domains,buckets,matchingTargets,matchingDetails,cellText,exportView,currentViewCSV,validateView,projectDashboard,visibleFacets} from '../integrations/javascript/evidence-model.mjs';
import {recordDetails} from '../design/prototype/evidence-reader.js';
import {storedProfile,readableExport} from '../design/prototype/profile-view.js';
import {demoProfile,taskSummary} from '../design/prototype/report-results.js';
const fixture=()=>JSON.parse(readFileSync(new URL('../integrations/fixtures/report-experience.json',import.meta.url),'utf8'));
test('cross-domain and multi-label counting preserves distinct source records',()=>{
 const p=fixture(),r=p.extraction.records[1];
 assert.deepEqual(domains(p,r),['agriculture','water']);
 assert.equal(filterRecords(p,{domain:['agriculture','water'],topic:['AGR-01']}).length,1);
 assert.equal(buckets(p,[r],'domain').reduce((n,b)=>n+b.recordIds.length,0),2);
 const before=structuredClone(p);projectDashboard(p);assert.deepEqual(p,before);
 assert.equal(projectDashboard(p).count_unit,'source_records');
});
test('target predicates match one variant and retain correct linked details',()=>{
 const p=fixture(),r=p.extraction.records[1];
 assert.equal(filterRecords(p,{topic:['AGR-01'],conditionality:['explicitly_conditional'],period:['2030']}).length,0);
 assert.equal(filterRecords(p,{topic:['AGR-01'],conditionality:['explicitly_conditional'],period:['2035']}).length,1);
 const actor={target_ids:[r.targets[0].local_id]},general={target_ids:[]};
 assert.deepEqual(matchingDetails(r,[actor,general],{period:['2035']}),[general]);
 assert.equal(matchingTargets(r,{period:['2035']})[0].value.raw_token,'50');
 assert.ok(!cellText(p,r,'targets',{period:['2035']}).includes('30 hectares'));
});
test('qualitative commitments, unmapped terms, observations and contexts stay distinct',()=>{
 const p=fixture();
 assert.ok(filterRecords(p,{},'targets').some(r=>!r.targets.length&&r.kind==='commitment'));
 assert.equal(filterRecords(p,{topic:['__unmapped']})[0].local_id,'design-r-10');
 assert.equal(filterRecords(p,{query:'repair circles'})[0].local_id,'design-r-10');
 assert.ok(filterRecords(p,{kind:['context']},'risk').length);
 assert.equal(filterRecords(p,{kind:['implementation_observation']})[0].reference_period,'2024');
 const financed=p.extraction.records[8];assert.equal(financed.targets.length,0);assert.ok(cellText(p,financed,'finance').includes('Financing source'));
});
test('saved view validation rejects missing IDs and unsupported presentation settings',()=>{
 const p=fixture(),v=defaultView(p);assert.deepEqual(validateView(p,v),[]);
 v.filters.hazards=['invented-new-hazard'];assert.ok(validateView(p,v).length);
 v.filters={};v.columns=[];assert.ok(validateView(p,v).length);
 v.columns=['statement'];v.sections=null;assert.ok(validateView(p,v).length);
 for(const patch of [{filters:null},{filters:{kind:'commitment'}},{filters:{kind:['commitment','commitment']}},{perspective:'toString'},{codebook:[]},{columns:['statement','toString']}])assert.ok(validateView(p,{...defaultView(p),...patch}).length);
});
test('filtered exports include cited context, scope, definitions, original English and CSV escaping',()=>{
 const p=fixture(),v=defaultView(p);v.filters.query='international financing';
 const result=exportView(p,v);assert.ok(result.records.length<p.extraction.records.length);assert.ok(result.definitions.topics.length);
 assert.ok(result.sources.some(s=>s.segments.some(x=>x.language==='ru')));
 assert.equal(result.profile_id,p.id);assert.match(result.narrative_scope,/not regenerated/);
 const before=structuredClone(p);p.extraction.records[0].label_en='=DANGEROUS()';v.filters={query:'=DANGEROUS'};
 const csv=currentViewCSV(p,v);assert.ok(csv.includes("'=DANGEROUS"));assert.ok(csv.includes('evidence_annex'));assert.ok(csv.includes('topic_definitions'));
 const html=readableExport(before,defaultView(before));assert.ok(html.includes('English segment'));assert.ok(html.includes('Current filtered view'));
});
test('archived definitions and all missing reasons appear in readable evidence',()=>{
 const p=fixture();p.validation_codebook.topics[0].definition='Archived special definition';p.extraction.records[0].labels.topic_ids=['CLM-01'];
 assert.ok(recordDetails(p,p.extraction.records[0]).includes('Archived special definition'));
 const html=recordDetails(p,p.extraction.records[11]);for(const word of ['Ambiguous','unreadable','not processed','Not applicable'])assert.ok(html.includes(word),word);
 assert.ok(!html.includes('<pre'));
});
test('earlier and empty demos do not retain dangling evidence or invented current findings',()=>{
 const old=demoProfile(fixture(),'country','earlier');
 const ids=new Set(old.extraction.records.map(r=>r.local_id));
 for(const f of [...old.report.headline_findings,...old.report.sections.flatMap(s=>s.findings)])assert.ok(f.citations.record_ids.every(id=>ids.has(id)));
 assert.equal(old.extraction.records.length,5);
 const empty=demoProfile(fixture(),'country','empty');assert.equal(empty.report.headline_findings.length,0);
 assert.ok(storedProfile({profile:empty,selection:{},history:[]}).includes('No extracted records available'));
 const emptyBrief=demoProfile(fixture(),'brief','empty');assert.ok(!taskSummary(emptyBrief,[]).includes('data-record'));
 const oldBrief=demoProfile(fixture(),'brief','earlier');assert.ok(!taskSummary(oldBrief,oldBrief.extraction.records).includes('conflicting deadlines'));
 const oldComparison=demoProfile(fixture(),'compare','earlier');assert.ok(!taskSummary(oldComparison,oldComparison.extraction.records).includes('25%'));
});
test('source observations and static narrative keep explicit scope and claim types',()=>{
 const p=fixture(),v=defaultView(p);v.filters.query='not-a-real-match';
 const html=storedProfile({profile:p,selection:{},history:[]},'brief',v);
 assert.ok(html.includes('0 of 12 source records'));assert.ok(html.includes('not been regenerated'));
 assert.ok(html.includes('Synthetic')||html.includes('SYNTHETIC'));assert.ok(!html.includes('canonical commitments'));
});

test('new and archived classifications render without mutating or guessing a migration',()=>{
 const current=fixture(),legacy=JSON.parse(readFileSync(new URL('../examples/v2/legacy-profile.json',import.meta.url),'utf8'));
 const before=structuredClone(legacy);
 assert.equal(cellText(current,current.extraction.records[0],'kind'),'Commitment');
 assert.match(cellText(legacy,legacy.extraction.records[0],'kind'),/Planned.*Action committed/);
 assert.match(recordDetails(legacy,legacy.extraction.records[0]),/Anticipate/);
 assert.ok(!recordDetails(current,current.extraction.records[0]).includes('undefined'));
 assert.ok(visibleFacets(current).risk_functions);
 for(const key of ['assertion_kind','documentation_status','drr_phases','resilience_functions','missing'])assert.ok(!(key in visibleFacets(current)));
 assert.ok(visibleFacets(legacy).drr_phases);
 assert.ok(!('risk_functions' in visibleFacets(legacy)));
 const view=defaultView(legacy);view.filters.kind=['commitment'];
 assert.ok(validateView(current,view).some(e=>e.includes('another method version')));
 assert.deepEqual(validateView(legacy,view),[]);
 const exported=exportView(legacy,view);assert.ok('assertion_kind' in exported.records[0]);
 assert.ok(!('assertion_kind' in exportView(current,defaultView(current)).records[0]));
 assert.deepEqual(legacy,before);
});

test('an integrated cross-sector measure keeps one record and one unallocated budget',()=>{
 const p=fixture(),r=p.extraction.records[0];r.labels.topic_ids=['AGR-01','ENE-01'];
 r.finance=[{kind:'approved_budget',description_en:'Shared programme budget; no sector allocation.',amount:{raw_token:'5'},currency:'million EUR',target_ids:[]}];
 p.extraction.records=[r];const v=defaultView(p);v.filters.domain=['agriculture','water','energy'];
 assert.equal(filterRecords(p,v.filters).length,1);
 assert.equal(buckets(p,[r],'domain').length,3);
 const exported=exportView(p,v);assert.equal(exported.record_count,1);assert.equal(exported.records[0].finance.length,1);
 assert.equal(cellText(p,r,'finance').match(/5 million EUR/g).length,1);
});

test('separate hazard actions do not produce a spurious flood-preparedness match',()=>{
 const p=fixture(),heat=structuredClone(p.extraction.records[0]),flood=structuredClone(heat);
 heat.local_id='heat-action';heat.labels.hazards=['extreme_heat'];heat.labels.risk_functions=['early_warning_preparedness'];
 flood.local_id='flood-action';flood.labels.hazards=['flood'];flood.labels.risk_functions=['recovery_reconstruction'];
 p.extraction.records=[heat,flood];
 assert.equal(filterRecords(p,{hazards:['flood'],risk_functions:['early_warning_preparedness']}).length,0);
 assert.equal(filterRecords(p,{hazards:['flood'],risk_functions:['recovery_reconstruction']})[0].local_id,'flood-action');
});
