import {AIClient,ROUTES,effortLabel,initialSelection,selectionProblem,selectModel,usageWindows} from '../../integrations/javascript/ai-client.mjs';

const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const storageKey='policytracker.ai.preferences.v1';
const usageLink='https://chatgpt.com/settings/usage';
const external=(url,text)=>`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${text} ↗</a>`;
const client=new AIClient();
export async function aiRequest(path,body){if(!client.csrf)await client.session();return client.request(path,body);}
const remembered=(()=>{try {return JSON.parse(localStorage.getItem(storageKey)) || {};}catch{return {};}})();
const defaultSelection=remembered.selection && Object.hasOwn(ROUTES,remembered.selection.route) && typeof remembered.selection.model==='string' && typeof remembered.selection.effort==='string' ? remembered.selection : initialSelection();
export const ai={status:null,selection:{...defaultSelection},defaults:{...defaultSelection},busy:false,error:'',notice:'',usage:null,usageError:'',login:null,job:null,prompt:'',limit:1024,loaded:false};
let notify=()=>{},initializing=null,loginTimer,jobTimer;
export function initializeAI(onChange) {
  notify=onChange;
  if(!initializing)initializing=(async()=>{try {await restoreSession();}catch(e){ai.error=e.message;}finally {ai.loaded=true;notify();}})();
  return initializing;
}
export function defaultAISelection(){return {...ai.defaults};}
export function selectionSummary(s){return `${ai.status?.models?.[s.route]?.find(m=>m.id===s.model)?.name || s.model} · ${effortLabel(s.effort)} · ${ROUTES[s.route]}`;}
export function modelControls(selection, prefix='ai', disabled=false) {
  const models=ai.status?.models?.[selection.route] || [],model=models.find(m=>m.id===selection.model);
  const problem=selectionProblem(selection,ai.status);
  const disabledAttr=disabled?'disabled':'';
  return `<div class="ai-model-controls"><label>Usage route<select id="${prefix}-route" ${disabledAttr}>${Object.entries(ROUTES).map(([id,label])=>`<option value="${id}" ${selection.route===id?'selected':''}>${label}</option>`).join('')}</select></label>
    <label>Model<select id="${prefix}-model" ${!models.length||disabled?'disabled':''}>${!model?`<option selected value="${esc(selection.model)}">${selection.model?esc(selection.model)+" · unavailable":"Choose a model"}</option>`:''}${models.map(m=>`<option value="${esc(m.id)}" ${m.id===selection.model?'selected':''}>${esc(m.name)}</option>`).join('')}</select></label>
    <label>Reasoning effort<select id="${prefix}-effort" ${!model||disabled?'disabled':''}>${!model?.efforts.includes(selection.effort)?`<option selected value="${esc(selection.effort)}">${esc(effortLabel(selection.effort))} · unavailable</option>`:''}${(model?.efforts||[]).map(e=>`<option value="${esc(e)}" ${e===selection.effort?'selected':''}>${esc(effortLabel(e))}</option>`).join('')}</select></label></div>
    ${model?.description?`<p class="ai-model-description">${esc(model.description)}</p>`:''}
    <p class="ai-route-note">${selection.route==='codex_chatgpt'?(ai.status?.chatgpt.connected?'Using ChatGPT plan':'Selected route: ChatGPT plan')+' · '+external(usageLink,'Manage usage'):'API usage is billed separately · '+external('https://platform.openai.com/usage','View API usage')}</p>
    ${problem?`<p class="ai-inline-warning">${esc(problem)}</p>`:''}`;
}
export function bindModelControls(root,selection,onChange,prefix='ai') {
  root.querySelector(`#${prefix}-route`)?.addEventListener('change',e=>{
    const route=e.target.value;
    Object.assign(selection,{route,model:'',effort:'default'});
    const models=ai.status?.models?.[route] || [];
    // A route change is explicit; require a deliberate model choice on that route.
    if(ai.defaults.route===route)Object.assign(selection,ai.defaults);
    else if(models.length===1)Object.assign(selection,selectModel(selection,models[0]));
    onChange();
  });
  root.querySelector(`#${prefix}-model`)?.addEventListener('change',e=>{
    const model=ai.status.models[selection.route].find(m=>m.id===e.target.value);
    if(model)Object.assign(selection,selectModel(selection,model));onChange();
  });
  root.querySelector(`#${prefix}-effort`)?.addEventListener('change',e=>{selection.effort=e.target.value;onChange();});
}
function usagePanel(){
  const windows=usageWindows(ai.usage);
  return `<section class="paper ai-usage"><div class="ai-section-heading"><h2>Usage & limits</h2><button data-ai="usage" ${ai.busy||!ai.status?.chatgpt.connected?'disabled':''}>Refresh usage</button></div>
    <p class="muted">ChatGPT account limits are shared across apps. API billing is separate.</p>
    ${windows.length?windows.map(w=>`<div class="ai-usage-window"><div><strong>${esc(w.name)}${w.windowDurationMins?' · '+esc(w.windowDurationMins>=1440?w.windowDurationMins/1440+' days':w.windowDurationMins>=60?w.windowDurationMins/60+' hours':w.windowDurationMins+' min'):''}</strong><span>${Math.round(w.remaining)}% remaining</span></div><progress max="100" value="${w.remaining}" aria-label="${esc(w.name)} quota remaining">${w.remaining}%</progress><small>${w.resetsAt?'Resets '+esc(new Date(w.resetsAt*1000).toLocaleString()):'Reset time unavailable'}</small></div>`).join(''):`<div class="ai-usage-empty">${esc(ai.usageError || (ai.status?.chatgpt.connected?'Refresh to see your account’s reported limits.':'Connect ChatGPT to view your account usage.'))}</div>`}
    <div class="ai-links">${external(usageLink,'Manage ChatGPT usage')}${external('https://platform.openai.com/usage','API usage dashboard')}</div>
    <p class="small-note muted">${ai.usage?.fetched_at?'Updated '+esc(new Date(ai.usage.fetched_at*1000).toLocaleTimeString())+'. ':''}Unavailable usage is shown as unknown. No dollar estimate is applied to ChatGPT quota.</p></section>`;
}
function resultPanel(){
  const job=ai.job;if(!job)return '<div class="ai-result-empty"><span aria-hidden="true">↗</span><h3>Ready when you are</h3><p>Test your exact model and effort with a short response. Each test uses the selected plan or API balance.</p></div>';
  const usage=job.usage;
  return `<div class="ai-result ${job.status==='failed'?'ai-result-error':''}"><div class="ai-section-heading"><strong>${{queued:'Starting…',running:'Waiting for response…',completed:'Response completed',failed:'Request failed'}[job.status]}</strong><span class="badge ${job.status==='completed'?'':'neutral'}">${esc(ROUTES[job.route])}</span></div>
    <p class="small-note muted">${esc(job.model)} · ${esc(effortLabel(job.effort))}</p>
    ${job.error?`<p role="alert">${esc(job.error.message)}</p>${job.error.code==='usage_limit'?external(job.route==='codex_chatgpt'?usageLink:'https://platform.openai.com/usage','Manage usage'):''}`:''}
    ${job.text?`<pre class="ai-response-text">${esc(job.text)}</pre>`:''}
    ${job.status==='completed'?`<p class="ai-verified">✓ Inference verified for this request</p><p class="small-note muted">Returned model: ${esc(job.actual_model || 'Not reported')} · Confirmed effort: ${esc(job.confirmed_effort?effortLabel(job.confirmed_effort):'Not reported')}</p>`:''}
    ${usage?`<div class="ai-token-row"><span>Input <strong>${usage.input_tokens??'—'}</strong></span><span>Output <strong>${usage.output_tokens??'—'}</strong></span><span>Total <strong>${usage.total_tokens??'—'}</strong></span></div>`:''}
    ${job.finished_at?`<p class="small-note muted">${Math.round((job.finished_at-job.started_at)*10)/10}s · Only completed requests verify access.</p>`:''}</div>`;
}
export function aiPage(){
  const chat=ai.status?.chatgpt,api=ai.status?.api,disabled=ai.busy||!ai.loaded||!!ai.login,problem=selectionProblem(ai.selection,ai.status);
  return `<div class="title-row"><div><div class="eyebrow">YOUR AI WORKSPACE</div><h1>AI connection</h1><p class="muted">Connect only when you are ready to run an analysis. Reading and preparing requests do not require a connection.</p></div><span class="ai-local-label">Local workspace</span></div>
    <div id="ai-feedback" aria-live="polite">${ai.error?`<div class="ai-alert" role="alert">${esc(ai.error)} <button data-ai="retry" ${ai.busy?'disabled':''}>Retry connection</button></div>`:''}${ai.notice?`<p class="ai-notice">${esc(ai.notice)}</p>`:''}</div>
    <div class="ai-connections">
      <section class="paper ai-connection ${chat?.connected?'is-connected':''}"><div class="ai-section-heading"><span class="ai-provider-icon" aria-hidden="true">◎</span><span class="badge ${chat?.connected?'':'neutral'}">${chat?.connected?'Connected':!ai.loaded?'Checking…':'Not connected'}</span></div><h2>Use your ChatGPT plan</h2><p>Use your local ChatGPT account for eligible model requests and connection tests.</p><p class="ai-connection-detail">${chat?.connected?`ChatGPT ${esc(chat.plan||'account')} · connected through local Codex`:chat?.available?'Your local Codex account is ready to connect.':esc(chat?.error||'Continue to ChatGPT to sign in securely.')}</p>
      <div class="ai-actions">${chat?.connected?`<button data-ai="disconnect-chatgpt" ${disabled?'disabled':''}>Disconnect</button>`:`<button class="primary" data-ai="${chat?.available?'connect-chatgpt':'login'}" ${disabled||ai.login?'disabled':''}>${chat?.available?'Use local ChatGPT account':'Continue with ChatGPT'}</button>`}${chat?.available?`<button class="text-link" data-ai="login" ${disabled?'disabled':''}>Switch account</button>`:''}${external(usageLink,'Manage usage')}</div><small>Signing in changes the local Codex account. Codex manages sign-in. Disconnect removes this workspace’s access; your Codex login stays available.</small></section>
      <section class="paper ai-connection ${api?.connected?'is-connected':''}"><div class="ai-section-heading"><span class="ai-provider-icon api" aria-hidden="true">⌘</span><span class="badge ${api?.connected?'':'neutral'}">${api?.connected?'Connected':'Separate billing'}</span></div><h2>Use the OpenAI API</h2><p>Connect your own API key for direct requests with an output-token limit.</p>${api?.connected?'<p class="ai-connection-detail">Key connected for this browser session. Stored in server memory only.</p>':`<form id="ai-key-form"><label for="ai-key">API key</label><div class="ai-key-row"><input id="ai-key" type="password" autocomplete="off" spellcheck="false" placeholder="sk-…" required ${disabled?'disabled':''}><button type="submit" ${disabled?'disabled':''}>Connect API</button></div></form>`}<div class="ai-actions">${api?.connected?`<button data-ai="disconnect-api" ${disabled?'disabled':''}>Disconnect API</button>`:''}${external('https://platform.openai.com/api-keys','Get an API key')}</div><small>API charges are separate from ChatGPT. Keys are never saved in browser storage or project files.</small></section>
    </div>
    ${ai.login?`<section class="ai-login-panel" role="status"><div><strong>Finish signing in to ChatGPT</strong><p>Complete the sign-in page, then return here. This page checks automatically.</p></div><div class="ai-actions">${external(ai.login.url,'Open sign-in page')}<button data-ai="cancel-login">Cancel</button></div></section>`:''}
    <details class="ai-advanced" ${chat?.connected||api?.connected?'open':''}><summary>Model preferences, connection test and usage</summary><div class="ai-workspace-grid"><section class="paper ai-model-panel"><div class="ai-section-heading"><div><div class="eyebrow">MODEL PREFERENCES</div><h2>Choose how AI works</h2></div><button data-ai="models" ${disabled||!(ai.selection.route==='codex_chatgpt'?chat?.connected:api?.connected)?'disabled':''}>Refresh models</button></div>
    ${modelControls(ai.selection,'ai',disabled)}
    <p class="small-note muted">Higher effort can take longer and consume more usage. Model availability is checked again before each request.</p>
    <div class="ai-actions"><button data-ai="save" ${disabled||problem?'disabled':''}>Save as default</button><span class="small-note muted">Applies to new analysis requests on this device.</span></div>
    <div class="ai-test-section"><h3>Try your connection</h3><p class="muted">A short test confirms that your selected model can respond.</p>
    ${ai.selection.route==='openai_api'?`<label class="ai-prompt-label">Optional test prompt<textarea id="ai-prompt" rows="3" maxlength="16000" placeholder="Ask a short question, or leave blank for a connection test." ${disabled?'disabled':''}>${esc(ai.prompt)}</textarea></label><label class="ai-limit-label">Maximum output tokens<select id="ai-limit" ${disabled?'disabled':''}>${[256,1024,4096,8192].map(n=>`<option ${ai.limit===n?'selected':''} value="${n}">${n.toLocaleString()}</option>`).join('')}</select></label><p class="small-note muted">This limit includes reasoning tokens. High effort may need a larger limit.</p>`:'<p class="small-note muted">ChatGPT sends a fixed connectivity prompt. Generate a Country Profile from the Regional tracker to translate and analyze its documents.</p>'}
    <button class="primary" data-ai="test" ${disabled||problem?'disabled':''}>${ai.busy?'Working…':'Test connection'}</button><p class="small-note muted">Uses ${ai.selection.route==='codex_chatgpt'?'your ChatGPT plan':'your API balance'}. Requests never switch billing routes automatically.</p></div></section>
    <aside class="ai-aside">${usagePanel()}<section class="paper ai-test-result" aria-live="polite" aria-atomic="false">${resultPanel()}</section></aside></div></details>`;
}
async function refresh(){ai.status=await client.request('/status');}
async function restoreSession(){
  ai.status=await client.init();
  clearTimeout(loginTimer);clearTimeout(jobTimer);jobTimer=null;
  ai.login=ai.status.login?.url?ai.status.login:null;ai.job=ai.status.job||null;
  if(ai.login)loginTimer=setTimeout(pollLogin,1000);
  ai.busy=!!ai.job&&['queued','running'].includes(ai.job.status);
  if(ai.busy)jobTimer=setTimeout(pollJob,1000);
}
async function fetchUsage(){try {ai.usage=await client.request('/usage');ai.usageError='';}catch(e){ai.usage=null;ai.usageError=e.message;}}
function welcome(){
  let seen=false;try{seen=localStorage.getItem('policytracker.chatgpt.welcome')==='yes';}catch{}
  if(seen)return;
  const dialog=document.createElement('dialog');dialog.className='ai-welcome';
  dialog.innerHTML='<h2>You’re using your ChatGPT plan</h2><p>Eligible requests in this workspace use your ChatGPT plan. You can review limits and manage usage in ChatGPT settings.</p><button class="primary">Got it</button>';
  document.body.append(dialog);dialog.setAttribute('aria-label','ChatGPT plan usage');
  dialog.querySelector('button').onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>{try{localStorage.setItem('policytracker.chatgpt.welcome','yes');}catch{}dialog.remove();});dialog.showModal();
}
async function action(fn){
  if(ai.busy)return;ai.busy=true;ai.error='';ai.notice='';notify();
  try {await fn();}catch(e){ai.error=e.message;}finally {ai.busy=!!jobTimer;notify();}
}
async function pollLogin(){
  if(!ai.login)return;
  try {const result=await client.request('/login/status');if(result.status==='completed'){ai.login=null;await refresh();await fetchUsage();ai.notice='ChatGPT connected. Choose a model and test your connection.';notify();welcome();return;}
    if(result.status!=='pending'){ai.login=null;ai.error='Sign-in did not complete. Continue with ChatGPT to try again.';notify();return;}}
  catch(e){ai.error=e.message;ai.login=null;notify();return;}
  loginTimer=setTimeout(pollLogin,2000);
}
async function pollJob(){
  jobTimer=null;
  try {ai.job=await client.request('/jobs/'+ai.job.id);notify();if(['queued','running'].includes(ai.job.status)){jobTimer=setTimeout(pollJob,1000);return;}
    if(ai.job.route==='codex_chatgpt')await fetchUsage();}
  catch(e){ai.error=e.message;}
  ai.busy=false;notify();
}
export function bindAI(root){
  bindModelControls(root,ai.selection,()=>{ai.error='';ai.notice='';notify();});
  root.querySelector('#ai-prompt')?.addEventListener('input',e=>ai.prompt=e.target.value);
  root.querySelector('#ai-limit')?.addEventListener('change',e=>ai.limit=Number(e.target.value));
  root.querySelector('#ai-key-form')?.addEventListener('submit',e=>{e.preventDefault();const input=root.querySelector('#ai-key');const key=input.value;input.value='';action(async()=>{await client.request('/api-key',{key});await refresh();ai.notice='API connected. Select the API route to choose a model.';});});
  root.querySelectorAll('[data-ai]').forEach(button=>button.addEventListener('click',()=>{
    const name=button.dataset.ai;
    if(name==='save'){ai.defaults={...ai.selection};try {localStorage.setItem(storageKey,JSON.stringify({selection:ai.defaults}));ai.notice='Default model saved for new analysis requests.';}catch{ai.notice='Default model set for this page. Browser storage is unavailable.';}notify();return;}
    if(name==='test'){
      if(ai.busy)return;ai.busy=true;ai.error='';notify();
      client.request('/jobs',{...ai.selection,kind:ai.selection.route==='openai_api'&&ai.prompt.trim()?'prompt':'test',prompt:ai.prompt,max_output_tokens:ai.limit})
        .then(job=>{ai.job=job;notify();pollJob();}).catch(e=>{ai.error=e.message;ai.busy=false;notify();});return;
    }
    action(async()=>{
      if(name==='retry'){await restoreSession();}
      if(name==='connect-chatgpt'){await client.request('/chatgpt/connect',{});await refresh();await fetchUsage();ai.notice='ChatGPT connected. Test your selected model to verify access.';welcome();}
      if(name==='login'){ai.login=await client.request('/login/start',{});ai.usage=null;await refresh();loginTimer=setTimeout(pollLogin,1000);}
      if(name==='cancel-login'){clearTimeout(loginTimer);await client.request('/login/cancel',{});ai.login=null;}
      if(name.startsWith('disconnect-')){const route=name==='disconnect-api'?'openai_api':'codex_chatgpt';await client.request('/disconnect',{route});if(route==='codex_chatgpt')ai.usage=null;await refresh();ai.notice='Connection removed from this workspace session.';}
      if(name==='models'){await client.request('/models',{route:ai.selection.route});await refresh();ai.notice='Model catalog refreshed. Your selection has been preserved.';}
      if(name==='usage')await fetchUsage();
    });
  }));
}
