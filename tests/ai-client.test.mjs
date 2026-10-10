import test from 'node:test';
import assert from 'node:assert/strict';
import {AIClient,initialSelection,selectionProblem,selectModel,usageWindows} from '../integrations/javascript/ai-client.mjs';

test('local preparation has enough time for cold parsing and OCR without changing model request timeouts',async t=>{
  const delays=[],original=setTimeout;
  t.mock.method(globalThis,'setTimeout',(fn,ms)=>{delays.push(ms);return original(fn,ms);});
  const client=new AIClient(async()=>({ok:true,json:async()=>({ready:true})}));
  await client.request('/preparation',{action:'inspect'});
  await client.request('/preparation',{action:'ocr'});
  await client.request('/country-runs',{});
  assert.deepEqual(delays,[390000,390000,105000]);
});

test('catalog and effort validation never changes a saved selection',()=>{
  const selection=initialSelection();
  const status={chatgpt:{connected:true},models:{codex_chatgpt:[{id:'another',efforts:['low']}]}};
  assert.match(selectionProblem(selection,status),/previous selection/);
  assert.equal(selection.model,'gpt-6-astra');
  status.models.codex_chatgpt=[{id:selection.model,efforts:['high']}];
  assert.match(selectionProblem(selection,status),/supported reasoning/);
  status.models.codex_chatgpt[0].efforts.push('xhigh');
  assert.equal(selectionProblem(selection,status),'');
  status.chatgpt.connected=false;
  assert.match(selectionProblem(selection,status),/Connect/);
});
test('explicit model change preserves effort when supported and otherwise uses its default',()=>{
  assert.equal(selectModel(initialSelection(),{id:'new',efforts:['high','xhigh'],default_effort:'high'}).effort,'xhigh');
  assert.equal(selectModel(initialSelection(),{id:'new',efforts:['default'],default_effort:'default'}).effort,'default');
});
test('usage keeps missing data unknown and clamps reported remaining quota',()=>{
  assert.deepEqual(usageWindows({buckets:[{primary:null,secondary:{usedPercent:null}}]}),[]);
  assert.equal(usageWindows({buckets:[{limitId:'codex',primary:{usedPercent:30}}]})[0].remaining,70);
  assert.equal(usageWindows({buckets:[{primary:{usedPercent:110}}]})[0].remaining,0);
});
test('client binds writes to same-origin session and CSRF without storing a key',async()=>{
  const calls=[];
  const client=new AIClient(async(path,options)=>{calls.push({path,options});return {ok:true,json:async()=>path.endsWith('/session')?{csrf:'synthetic-csrf'}:{connected:true}};});
  await client.init();await client.request('/api-key',{key:'synthetic-test-value'});
  assert.equal(calls[2].options.headers['X-PolicyTracker-CSRF'],'synthetic-csrf');
  assert.equal(calls[2].options.credentials,'same-origin');
  assert.equal(client.key,undefined);
});
test('client propagates actionable quota errors',async()=>{
  const client=new AIClient(async()=>({ok:false,json:async()=>({error:{code:'usage_limit',message:'Review usage'}})}));
  await assert.rejects(client.request('/jobs',{}),e=>e.code==='usage_limit'&&e.message==='Review usage');
});

test('a dropped status read retries once, including a reset while reading its body',async()=>{
  for(const duringBody of [false,true]) {
    let calls=0;
    const client=new AIClient(async()=>{
      calls++;
      if(calls===1&&!duringBody)throw new TypeError('Failed to fetch');
      return {ok:true,json:async()=>{if(calls===1)throw new TypeError('Connection reset');return {status:'completed'};}};
    });
    assert.deepEqual(await client.request('/jobs/test'),{status:'completed'});
    assert.equal(calls,2);
  }
});

test('network recovery never repeats writes and stops after two failed reads',async()=>{
  for(const body of [undefined,{model:'test'}]) {
    let calls=0;
    const client=new AIClient(async()=>{calls++;throw new TypeError('Failed to fetch');});
    await assert.rejects(client.request('/jobs',body),TypeError);
    assert.equal(calls,body===undefined?2:1);
  }
});
