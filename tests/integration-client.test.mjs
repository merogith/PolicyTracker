import test from 'node:test';
import assert from 'node:assert/strict';
import { PolicyTrackerClient, PolicyTrackerError } from '../integrations/javascript/client.mjs';

test('encodes workspace/country, retains conditional read and server token', async () => {
  let seen;
  const client = new PolicyTrackerClient({baseUrl:'https://service.example.invalid/',workspaceId:'team/1',getToken:async()=> 'synthetic-token',fetchImpl:async(url,options)=>{seen={url,options};return new Response(JSON.stringify({revision:3}),{status:200,headers:{ETag:'"p3"'}});}});
  const result=await client.getPrime('KAZ',{etag:'"p2"'});
  assert.equal(seen.url,'https://service.example.invalid/v1/workspaces/team%2F1/countries/KAZ/prime');
  assert.equal(seen.options.headers['If-None-Match'],'"p2"');
  assert.equal(seen.options.headers.Authorization,'Bearer synthetic-token');
  assert.equal(result.etag,'"p3"');
  assert.equal(result.data.revision,3);
});
test('a run cannot be started without an idempotency key',()=>{
  const client=new PolicyTrackerClient({baseUrl:'/service',workspaceId:'team',fetchImpl:()=>{throw Error('must not dispatch');}});
  assert.throws(()=>client.startRun({}),/idempotency key/);
});
test('pinning cannot omit concurrency precondition',()=>{
  const client=new PolicyTrackerClient({baseUrl:'/service',workspaceId:'team',fetchImpl:()=>{throw Error('must not dispatch');}});
  assert.throws(()=>client.selectPrime('KAZ',{mode:'pinned',report_id:'r'}),/ETag/);
});
test('304 does not try to parse an empty response',async()=>{
  const client=new PolicyTrackerClient({baseUrl:'/service',workspaceId:'team',fetchImpl:async()=>new Response(null,{status:304})});
  assert.equal((await client.getPrime('KAZ')).status,304);
});
test('API errors retain status and correlation ID',async()=>{
  const client=new PolicyTrackerClient({baseUrl:'/service',workspaceId:'team',fetchImpl:async()=>new Response(JSON.stringify({code:'scope_denied',message:'Not available',request_id:'req-demo'}),{status:403})});
  await assert.rejects(client.getPrime('KAZ'),e=>e instanceof PolicyTrackerError && e.requestId==='req-demo' && e.status===403);
});
