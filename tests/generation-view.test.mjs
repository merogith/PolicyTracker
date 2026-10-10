import test from 'node:test';
import assert from 'node:assert/strict';
import {runProgress,preparationSummary,pageReviewForm,createGeneration} from '../design/prototype/generation-view.js';

const run={stage:'translate',status:'running',message:'Preparing English',completed:2,total:6,selection:{route:'openai_api',model:'gpt-6-astra',effort:'high'}};
test('progress reports completed units with one active step and a stop action',()=>{
  const html=runProgress(run);
  assert.match(html,/2 of 6 complete/);assert.match(html,/data-run-action="stop"/);
  assert.equal((html.match(/aria-current="step"/g)||[]).length,1);
  assert.doesNotMatch(html,/%/);
});

test('legacy review failures offer automatic recovery instead of a futile resume, including older saved runs',()=>{
  for(const extra of [{required_action:'review_sources',can_resume:false},{error:'NDC 3.0: 1 pages need review. page 15: text needs inspection'}]){
    const html=runProgress({...run,status:'failed',stage:'prepare',...extra});
    assert.match(html,/automatic recovery/);assert.doesNotMatch(html,/Resume run/);
  }
});
test('source preflight shows all affected documents and physical pages with escaped source labels',()=>{
  const html=preparationSummary({ready:false,pages_needing_review:2,documents:[{document_id:'doc-a',title:'First <script>',pages:[{page:15,concerns:['raster_content_may_contain_text']}]},{document_id:'doc-b',title:'Second',pages:[{page:83,concerns:['sparse_text']}]}]});
  assert.match(html,/2 pages need review/);assert.match(html,/Review page 15/);assert.match(html,/Review page 83/);
  assert.match(html,/First &lt;script&gt;/);assert.doesNotMatch(html,/<script>/);
});
test('page review keeps OCR drafts unapproved and requires a note and visual confirmation',()=>{
  const page={title:'Test',document_id:'doc-a',page:2,text:'<script>',candidate:{text:'Draft',note:'Uncertain table cells'},has_candidate:true,renderer_available:true,ocr_available:false};
  const draft={method:'reviewed_text',text:'<script>',note:'',confirmed:false,language:'eng'};
  const html=pageReviewForm(page,draft);
  assert.match(html,/Unapproved draft/);assert.match(html,/Uncertain table cells/);
  assert.match(html,/data-review-save disabled/);assert.match(html,/data-review-ocr disabled/);
  assert.match(html,/&lt;script&gt;/);assert.doesNotMatch(html,/<script>/);
  assert.doesNotMatch(pageReviewForm(page,{...draft,note:'Checked each cell',confirmed:true}),/data-review-save disabled/);
});
test('failure details are escaped, with resume and no completion claim',()=>{
  const html=runProgress({...run,status:'failed',error:'<script>bad()</script>'});
  assert.match(html,/&lt;script&gt;/);assert.doesNotMatch(html,/<script>/);
  assert.match(html,/Resume run/);assert.doesNotMatch(html,/Your Country Profile is ready/);
});
test('stopping cannot issue a duplicate stop; completed runs link to the profile',()=>{
  assert.match(runProgress({...run,status:'stopping'}),/data-run-action="stop" disabled/);
  const html=runProgress({...run,status:'completed',stage:'validate'});
  assert.match(html,/View Country Profile/);assert.doesNotMatch(html,/Resume run|data-run-action="stop"/);
});

test('polling notices a different completed run and retries a failed profile refresh',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});
 const old={...run,id:'run-old',profile_id:'profile-old',document_ids:['doc'],status:'completed'},fresh={...old,id:'run-new',profile_id:'profile-new'};
 let latest=old,fail=false;const saved=[],viewed=[],listeners={};
 const root={isConnected:true,innerHTML:'',querySelectorAll:()=>[],querySelector:selector=>selector==='[data-view]'?{addEventListener:(_,fn)=>{listeners.view=fn;}}:null};
 const generation=createGeneration({request:async()=>({runs:[latest],active_country:null}),onSaved:async code=>{saved.push(code);if(fail)throw Error('Temporary read failure');},onView:(...args)=>viewed.push(args)});
 const settle=async()=>{for(let i=0;i<8;i++)await Promise.resolve();};
 generation.mount(root,'KAZ',[{id:'doc',title:'Example',pages:1}]);await settle();
 assert.deepEqual(saved,['KAZ']);
 latest=fresh;fail=true;t.mock.timers.tick(2500);await settle();
 assert.equal(saved.length,2);assert.match(root.innerHTML,/Temporary read failure/);
 fail=false;t.mock.timers.tick(2500);await settle();assert.equal(saved.length,3);assert.doesNotMatch(root.innerHTML,/Temporary read failure/);
 t.mock.timers.tick(2500);await settle();assert.equal(saved.length,3,'The same completed run refreshes only once after success');
 listeners.view();assert.deepEqual(viewed,[['KAZ','profile-new']]);
 root.isConnected=false;t.mock.timers.reset();
});

test('an unavailable inventory never looks empty or starts a run; retry restores document choices',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});
 const requests=[],root={isConnected:true,innerHTML:'',querySelectorAll:()=>[],querySelector:()=>null};
 const generation=createGeneration({request:async(path,body)=>{requests.push({path,body});return {runs:[],active_country:null};},onConnect:()=>assert.fail('An unknown inventory cannot proceed to generation')});
 generation.mount(root,'ALB',[],{sourceAvailabilityUnknown:true});generation.open();
 assert.match(root.innerHTML,/Local source availability is unknown/);assert.doesNotMatch(root.innerHTML,/0 documents/);assert.match(root.innerHTML,/data-generate disabled/);
 await new Promise(setImmediate);assert.ok(requests.every(r=>r.body===undefined));
 generation.mount(root,'ALB',[{id:'a',title:'Original',pages:1}]);
 assert.match(root.innerHTML,/1 document selected/);assert.doesNotMatch(root.innerHTML,/data-generate disabled/);
 root.isConnected=false;await new Promise(setImmediate);t.mock.timers.reset();
});

test('Stop immediately acknowledges a pending request, prevents duplicates and explains the saved stopping state',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});
 let latest={...run,id:'run-alb',document_ids:['doc']},resolveStop;const writes=[],listeners={};
 const root={isConnected:true,innerHTML:'',querySelectorAll:()=>[],querySelector:selector=>selector==='[data-stop]'?{addEventListener:(_,fn)=>{listeners.stop=fn;}}:null};
 const generation=createGeneration({request:async(path,body)=>{
  if(body===undefined)return {runs:[latest],active_country:'ALB'};
  writes.push(path);return new Promise(resolve=>{resolveStop=resolve;});
 }});
 const settle=async()=>{for(let i=0;i<8;i++)await Promise.resolve();};
 generation.mount(root,'ALB',[{id:'doc',title:'Original',pages:1}]);await settle();
 listeners.stop();
 assert.match(root.innerHTML,/data-stop disabled/);assert.match(root.innerHTML,/Requesting stop/);
 listeners.stop();assert.equal(writes.length,1,'Clicking again while Stop is pending never repeats the request');
 latest={...latest,status:'stopping',message:'Finishing active requests, then stopping. Their valid results will be saved.'};resolveStop(latest);await settle();
 assert.match(root.innerHTML,/Stopping your profile/);assert.match(root.innerHTML,/data-stop disabled/);assert.match(root.innerHTML,/active requests/);
 listeners.stop();assert.equal(writes.length,1,'An acknowledged stop cannot issue another stop');
 root.isConnected=false;t.mock.timers.reset();
});

test('another active country explains the disabled generation control and blocks programmatic starts until released',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});
 let activeCountry='ALB';const requests=[],listeners={};
 const previous={...run,id:'run-kaz',status:'stopped',document_ids:['doc']};
 const root={isConnected:true,innerHTML:'',querySelectorAll:()=>[],querySelector:selector=>selector==='[data-resume]'?{addEventListener:(_,fn)=>{listeners.resume=fn;}}:null};
 const generation=createGeneration({request:async(path,body)=>{requests.push({path,body});return {runs:[previous],active_country:activeCountry};},onConnect:()=>assert.fail('An active country must block starts before requesting connection')});
 const settle=async()=>{for(let i=0;i<8;i++)await Promise.resolve();};
 generation.mount(root,'KAZ',[{id:'doc',title:'Original',pages:1}]);await settle();
 assert.match(root.innerHTML,/data-generate disabled/);assert.match(root.innerHTML,/data-resume disabled/);assert.match(root.innerHTML,/ALB.*active/);assert.match(root.innerHTML,/finish or stop/);
 generation.open();listeners.resume();await settle();assert.ok(requests.every(r=>r.body===undefined));
 activeCountry=null;t.mock.timers.tick(2500);await settle();
 assert.doesNotMatch(root.innerHTML,/data-generate disabled|data-resume disabled|ALB.*active/);
 root.isConnected=false;t.mock.timers.reset();
});
