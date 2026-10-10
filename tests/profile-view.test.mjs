import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {storedProfile,filterRecords} from '../design/prototype/profile-view.js';

import {recordDetails,evidenceReader} from '../design/prototype/evidence-reader.js';
import {defaultView} from '../integrations/javascript/evidence-model.mjs';
import {readableExport} from '../design/prototype/profile-view.js';
import {exportView,currentViewCSV} from '../integrations/javascript/evidence-model.mjs';
const read = name => JSON.parse(readFileSync(new URL(`../examples/v2/${name}.json`, import.meta.url), 'utf8'));
function data() {
  const source = read('synthetic-input'), translation = read('translation');
  return {selection:{},history:[],profile:{id:'immutable-version',country_code:'KAZ',synthetic:true,
    provenance_note:'Invented fixture',created_at:'2026-10-09',archive:{},
    extraction:read('extraction'),report:read('prime-report'),sources:[{title:'Example',sha256:'a'.repeat(64),pages:1,
      segments:Object.entries(source.source_segments).map(([id,text])=>({id,text,page:1,language:'ru',english_text:translation.segments.find(s=>s.segment_id===id).english_text,translation_method:'machine_translation'}))}]}};
}

test('extraction notes remain visible and escaped in readers and every current-view export',()=>{
 const d=data(), p=d.profile, note='Sample only <script>not executable</script>';
 p.extraction.notes=[note];const v=defaultView(p);
 assert.match(storedProfile(d),/Extraction notes/);
 assert.ok(!storedProfile(d).includes('<script>not executable'));
 assert.match(readableExport(p,v),/Sample only &lt;script&gt;/);
 assert.deepEqual(exportView(p,v).extraction_notes,[note]);
 assert.ok(currentViewCSV(p,v).includes(note));
 delete p.extraction.notes;assert.doesNotThrow(()=>storedProfile(d));
});

test('saved evidence is escaped and exports stay bound to its version and scope',()=>{
  const d=data();d.profile.extraction.records[0].label_en='<img src=x onerror=alert(1)>';
  d.profile.sources[0].segments[0].english_text='<script>bad()</script>';
  const html=storedProfile(d,'commitments')+recordDetails(d.profile,d.profile.extraction.records[0]);
  assert.ok(!html.includes('<img')&&!html.includes('<script>'));
  assert.match(html,/&lt;img/);assert.match(html,/&lt;script/);
  assert.match(html,/version=immutable-version&amp;synthetic=1/);
  assert.match(html,/Condition: Subject to international financing/);
});

test('ranges, source limitations and analyst suggestions remain explicit in views',()=>{
  const d=data(), target=d.profile.extraction.records[0].targets[0];
  target.comparator='range';target.value=null;target.lower={raw_token:'20'};target.upper={raw_token:'30'};
  assert.match(recordDetails(d.profile,d.profile.extraction.records[0]),/20–30/);
  const finding=d.profile.report.headline_findings[0];finding.kind='analyst_suggestion';finding.limitations=['Only the supplied scope'];
  const overview=storedProfile(d,'brief');
  assert.match(overview,/Analyst suggestion/);assert.match(overview,/Only the supplied scope/);
});

test('generated provenance and unresolved source links are visible without claiming a merged count',()=>{
  const d=data();d.profile.synthetic=false;d.profile.generation={selection:{route:'openai_api',model:'test-model',effort:'high'}};
  d.profile.reconciliation={relations:[{kind:'contradicts',source_record_ids:['r-1'],target_record_ids:['r-2'],evidence_ids:['e-1'],reason:'<b>Different deadlines</b>'}],groups:[],issues:['Timing needs review']};
  const html=storedProfile(d,'commitments')+recordDetails(d.profile,d.profile.extraction.records[0]);
  assert.match(html,/GENERATED COUNTRY PROFILE/);assert.doesNotMatch(html,/Generation method is not verified/);
  assert.match(html,/&lt;b&gt;Different deadlines&lt;\/b&gt;/);assert.match(html,/Timing needs review/);
  assert.match(html,/not a count of unique commitments/);
  assert.match(html,/No records are automatically merged/);
});

test('overview keeps priorities, questions and inspectable contextual quotations',()=>{
  const d=data();
  d.profile.report.prioritized_commitments=[{commitment_id:'r-1',reason:'Explicit financing condition',evidence_ids:['e-1']}];
  d.profile.report.followup_questions=[{...structuredClone(d.profile.report.headline_findings[0]),kind:'analyst_suggestion',text_en:'What financing is secured?'}];
  const html=storedProfile(d,'brief')+evidenceReader(d.profile,['e-1']);
  for(const text of ['Priorities and their basis','Explicit financing condition','What financing is secured?','Inspect evidence','Linked context','Original quotation','English segment'])assert.ok(html.includes(text),text);
  assert.match(html,/К 2030/);assert.match(html,/By 2030/);
});

test('filters use archived topic relationships and retain each cross-sector record once',()=>{
  const d=data(),r=d.profile.extraction.records[0];
  d.profile.validation_codebook={topics:[{id:'CLM-04',name:'Archived warning topic',domain_ids:['climate','water'],definition:'Archived meaning',routing_rule:'Archived rule'}],domains:[{id:'climate',name:'Climate'},{id:'water',name:'Water'}],dimensions:[]};
  assert.equal(filterRecords(d.profile,{query:'archived warning',domain:'water',kind:'commitment',hazard:'flood',risk_functions:['early_warning_preparedness']}).length,1);
  assert.equal(filterRecords(d.profile,{domain:'energy'}).length,0);
  assert.equal(filterRecords(d.profile,{kind:'result_observation'}).length,0);
  assert.equal(filterRecords(d.profile,{query:'nonexistent'}).length,0);
  assert.deepEqual(filterRecords(d.profile),[r]);
  const html=storedProfile(d,'commitments')+recordDetails(d.profile,d.profile.extraction.records[0]);
  assert.match(html,/Archived meaning/);assert.match(html,/archived validation codebook/);
  assert.match(html,/Full report includes all saved records/);
});

test('repeated statements keep both source records, locators and proposed differences',()=>{
  const d=data(), p=d.profile;
  p.sources[0].title='Earlier policy';
  const later=structuredClone(p.sources[0]);later.title='Later policy <draft>';
  later.segments=later.segments.map(s=>({...s,id:`later:${s.id}`,page:4}));
  p.sources.push(later);
  const record=structuredClone(p.extraction.records[0]);record.local_id='later:r-1';
  record.evidence_ids=record.evidence_ids.map(id=>`later:${id}`);
  p.extraction.records.push(record);
  p.extraction.evidence.push(...p.extraction.evidence.map(e=>({...e,local_id:`later:${e.local_id}`,segment_id:`later:${e.segment_id}`,context_evidence_ids:e.context_evidence_ids.map(id=>`later:${id}`)})));
  p.reconciliation={groups:[],changes:[],relations:[{kind:'unresolved',source_record_ids:['r-1'],target_record_ids:['later:r-1'],reason:'Same action; the later financing condition needs interpretation.',evidence_ids:['e-1','later:e-1']}],issues:[]};
  const before=structuredClone(p), html=storedProfile(d,'commitments');
  assert.deepEqual(p,before,'Rendering must not merge or alter extracted records');
  assert.equal((html.match(/data-profile-row=/g)||[]).length,2);
  assert.match(html,/2 of 2 source records shown/);
  assert.match(html,/Earlier policy · page 1/);
  assert.match(html,/Later policy &lt;draft&gt; · page 4/);
  assert.match(html,/unresolved · proposed/);
  assert.match(html,/Same action; the later financing condition needs interpretation/);
  assert.equal(filterRecords(p,{query:record.label_en}).length,2);
});

test('citations open their archived physical PDF page and disclose automatic transcription',()=>{
 const p=data().profile,d=p.sources[0];
 d.document_id='document-with-scan';d.path='data/sources/example/original.pdf';
 d.page_checks=[{page:1,automatic:{method:'vision',status:'partial',notes:['Unclear table cell <value>']}}];
 const html=evidenceReader(p,['e-1']);
 assert.match(html,/\/api\/ai\/documents\/immutable-version\/document-with-scan\?inline=1#page=1/);
 assert.match(html,/AI image transcription/);assert.match(html,/Page coverage: partial/);
 assert.match(html,/Unclear table cell &lt;value&gt;/);assert.doesNotMatch(html,/documents\/current\//);
 d.page_checks=[{page:1,automatic:{method:'native',status:'complete',notes:[]}}];
 assert.match(evidenceReader(p,['e-1']),/Native PDF text/);
 d.page_checks=[{page:1,review:{method:'ocr',note:'Checked against original'}}];
 assert.match(evidenceReader(p,['e-1']),/Human-reviewed OCR transcription/);
 p.presentation_fixture=true;assert.doesNotMatch(evidenceReader(p,['e-1']),/Open original PDF/);
});

test('downloaded HTML retains evidence and provenance without unusable local API links',()=>{
 const p=data().profile,d=p.sources[0];d.document_id='archived-document';d.path='data/sources/example/original.pdf';
 d.page_checks=[{page:1,automatic:{method:'vision',status:'partial',notes:['Unclear table cell']}}];
 const html=readableExport(p,defaultView(p));
 assert.doesNotMatch(html,/href="\/api\/ai\/documents\//);
 assert.match(html,/Open original PDFs from this saved version in the local tracker/);
 assert.match(html,/Original quotation/);assert.match(html,/AI image transcription/);
 assert.match(html,/Unclear table cell/);assert.match(html,/immutable-version/);
 assert.match(recordDetails(p,p.extraction.records[0]),/archived-document\?inline=1#page=1/,'The in-app reader retains its version-bound page link');
});
