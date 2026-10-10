import test from 'node:test';
import assert from 'node:assert/strict';

test('retry restores the active request lock and clears stale session results after a restart', async t => {
  const timers = new Map();let nextTimer = 0;
  t.mock.method(globalThis, 'setTimeout', (fn, delay) => {const id = ++nextTimer;timers.set(id, {fn, delay});return id;});
  t.mock.method(globalThis, 'clearTimeout', id => timers.delete(id));
  let job = {id:'recovered-job',status:'running',route:'openai_api'};
  t.mock.method(globalThis, 'fetch', async path => ({ok:true,json:async () => {
    if (path.endsWith('/session')) return {csrf:'test-session'};
    if (path.endsWith('/status')) return {chatgpt:{connected:false},api:{connected:true},models:{},job};
    if (path.endsWith('/jobs/recovered-job')) return {...job,status:'completed'};
    throw new Error('Unexpected request: ' + path);
  }}));
  const {ai, bindAI, aiPage} = await import('../design/prototype/ai-view.js?recovery-test');
  ai.loaded=true;
  let retry;
  const button={dataset:{ai:'retry'},addEventListener:(name,fn)=>{retry=fn;}};
  bindAI({querySelector:()=>null,querySelectorAll:selector=>selector==='[data-ai]'?[button]:[]});
  retry();await new Promise(setImmediate);
  assert.equal(ai.busy,true);
  assert.equal(ai.job.id,'recovered-job');
  assert.match(aiPage(),/data-ai="test" disabled/);
  const timer=[...timers.entries()].find(([,value])=>value.delay===1000);
  assert.ok(timer);timers.delete(timer[0]);await timer[1].fn();
  assert.equal(ai.busy,false);
  assert.equal(ai.job.status,'completed');
  ai.login={url:'https://auth.openai.com/authorize?state=synthetic'};
  job=null;
  retry();await new Promise(setImmediate);
  assert.equal(ai.job,null);
  assert.equal(ai.login,null);
  assert.equal(ai.busy,false);
});
