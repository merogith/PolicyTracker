import test from 'node:test';
import assert from 'node:assert/strict';
import {renderOperation,operationCSV,operationHistory,readableOperationExport} from '../design/prototype/operations-view.js';

const result=()=>({id:'analysis-test',created_at:'2026-10-09',synthetic:true,request:{task:'compare',requested_fields:['targets'],output:{artifact:'comparison_matrix'}},
 sources:[{document_id:'source',title:'<script>document</script>',country_code:'KAZ',pages:1,sha256:'test',segments:[]}],
 extraction:{records:[],evidence:[]},evidence_table:[{label_en:'Wrong table for comparison'}],limitations:['Synthetic'],
 output:{groups:[{group_id:'a',label:'Earlier'},{group_id:'b',label:'Later'}],rows:[{dimension:'targets',cells:[{group_id:'a',state:'not_found_in_scope',findings:[]},{group_id:'b',state:'not_found_in_scope',findings:[]}],comparability:'not_comparable',comparability_reason:'Different baselines'}],synthesis:[],exclusions:[],limitations:[]}});
test('analysis history does not offer resume for source preparation failures',()=>{
 const html=operationHistory([{id:'analysis',status:'failed',stage:'prepare',required_action:'review_sources',can_resume:false,created_at:'2026-10-09',operation:{task:'extract'},document_ids:['doc']}],{tasks:[{id:'extract',label:'Extract'}]});
 assert.doesNotMatch(html,/Resume run/);assert.match(html,/automatic recovery/);
});
test('comparison renders requested matrix and exports matrix rows rather than evidence projection',()=>{
 const r=result(),html=renderOperation(r).body,csv=operationCSV(r);
 assert.match(html,/<th>Earlier<\/th><th>Later<\/th>/);assert.match(html,/Different baselines/);
 assert.ok(!html.includes('<script>'));assert.match(html,/&lt;script&gt;/);
 assert.match(csv,/'?"dimension"/);assert.ok(!csv.includes('Wrong table'));
});
test('empty extraction CSV stays empty instead of silently exporting documents',()=>{
 const r=result();r.request.task='extract';r.evidence_table=[];
 const csv=operationCSV(r);assert.equal(csv.split('\r\n').length,1);assert.ok(!csv.includes('document'));
});
test('CSV escapes source-controlled spreadsheet formulas',()=>{
 const r=result();r.request.task='extract';r.evidence_table=[{label_en:'=HYPERLINK("bad")'}];
 assert.match(operationCSV(r),/'=HYPERLINK/);
 r.evidence_table=[{label_en:'  =HYPERLINK("bad")'},{label_en:'\n@SUM(1)'}];
 assert.match(operationCSV(r),/'  =HYPERLINK/);assert.match(operationCSV(r),/'\n@SUM/);
});

test('downloaded analysis HTML retains every page and version without local session links',()=>{
 const r=result();r.request.task='translate';r.sources[0].path='data/sources/example.pdf';
 r.sources[0].segments=[1,2].map(page=>({id:'s'+page,page,text:'Original '+page,english_text:'English '+page,translation_method:'identity',translation_notes:['Read carefully']}));
 assert.match(renderOperation(r).body,/href="\/api\/ai\/documents/);
 const html=readableOperationExport(r);
 assert.match(html,/Saved version analysis-test/);assert.match(html,/English 2/);assert.match(html,/Read carefully/);
 assert.doesNotMatch(html,/href="\/api\/|<button\b|<select\b| hidden[ >]/);
});

test('unfinished and failed analyses remain visible outside unpublished result moderation',()=>{
 const runs=['running','stopping','stopped','failed','completed'].map(status=>({id:status,status,published:false,operation:{task:'extract'},created_at:'2026-10-10',document_ids:['doc'],message:status}));
 const html=operationHistory(runs,{tasks:[{id:'extract',label:'Extract'}]});
 const [visible,moderated]=html.split('<details><summary>Unpublished results');
 assert.match(visible,/Stop after current request/);assert.match(visible,/data-id="failed"/);assert.match(visible,/data-id="stopped"/);
 assert.match(moderated,/ · 1/);assert.match(moderated,/data-operation="completed"/);
});
test('saved translation qualifications remain visible and escaped in readable exports',()=>{
 const r=result();r.sources[0].segments=[{id:'s1',page:1,translation_method:'identity',text:'Original',english_text:'Original',translation_notes:['Sample only <script>bad()</script>']}];
 const html=renderOperation(r).body;
 assert.match(html,/Translation notes:/);assert.match(html,/Sample only &lt;script&gt;bad\(\)&lt;\/script&gt;/);
 assert.ok(!html.includes('<script>bad()'));
});

test('extraction notes survive analysis reading and CSV without becoming executable markup',()=>{
 const r=result();r.extraction.notes=['Only supplied pages <b>reviewed</b>'];
 assert.match(renderOperation(r).body,/Extraction notes/);
 assert.match(renderOperation(r).body,/&lt;b&gt;reviewed/);
 assert.match(operationCSV(r),/Only supplied pages/);
});
