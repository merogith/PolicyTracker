import {ai,aiRequest,defaultAISelection,selectionSummary,modelControls,bindModelControls} from './ai-view.js';
import {selectionProblem} from '../../integrations/javascript/ai-client.mjs';

const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const runStages=[['prepare','Read sources'],['translate','English text'],['extract','Evidence'],['reconcile','Duplicates & conflicts'],['overview','Overview'],['validate','Check & save']];
const active=run=>run&&['running','stopping'].includes(run.status);
export const requiresReview=run=>run?.required_action==='review_sources'||(run?.stage==='prepare'&&/text needs inspection|pages need review|source page/.test(run.error||''));
const canResume=run=>['stopped','failed'].includes(run.status)&&run.can_resume!==false&&!requiresReview(run);
const reason=value=>({sparse_text:'Little or no extracted text',damaged_text:'Damaged text characters',rotated_page:'Rotated layout',raster_content_may_contain_text:'Image may contain text',vector_content_may_convey_structure:'Table or chart structure needs image reading'}[value]||(/^(parse|inspection)_failed:/.test(value)?'PDF text or layout could not be read':value));

export function preparationSummary(report){
  if(!report)return '<p class="small-note">Check the selected documents before generating. This reads local files without using AI.</p>';
  return `<div class="preparation-summary" role="status"><strong>${report.ready?'Selected documents are ready for generation':!report.pages_needing_review?'Selected documents could not be prepared':`${report.pages_needing_review} ${report.pages_needing_review===1?'page needs':'pages need'} review before generation`}</strong><p class="small-note">${report.ready?'Page checks passed. This does not certify analytical accuracy.':'Open each flagged page, compare its text with the original, and save a checked transcription. Use OCR for scans; charts and tables still need visual review.'}</p></div>
    ${report.documents.map(doc=>`<div class="preparation-document"><strong>${esc(doc.title)}</strong><p class="small-note">${doc.ready?`Ready · ${doc.total_pages} pages · ${doc.reviewed_pages} reviewed`:doc.error?esc(doc.error):`${doc.pages.length} pages need review`}</p>${(doc.reviewed_page_numbers||[]).length?`<details><summary>Saved page reviews</summary>${doc.reviewed_page_numbers.map(n=>`<button data-review-document="${esc(doc.document_id)}" data-review-page="${n}">View reviewed page ${n}</button>`).join('')}</details>`:''}${doc.pages.map(p=>`<button class="preparation-page" data-review-document="${esc(doc.document_id)}" data-review-page="${p.page}">Review page ${p.page}<span>${esc(p.review_error||p.concerns.map(reason).join(' · '))}</span></button>`).join('')}</div>`).join('')}`;
}

export function pageReviewForm(page,draft,busy=false){
  const locked=!!(page.review||page.review_error),disabled=busy||locked?'disabled':'';
  return `<section class="page-review" aria-label="Source page review"><div class="run-heading"><h3 tabindex="-1">${esc(page.title)} · Physical page ${page.page}</h3><button data-review-close ${busy?'disabled':''}>Close page review</button></div>
    <p class="small-note">Compare every heading, number, table cell, chart label and footnote. Preserve unclear source content as unclear; do not invent missing words or values. The original PDF stays unchanged.</p>
    ${page.review_error?`<p class="run-error">${esc(page.review_error)}. Preserve the existing receipt before a deliberate correction.</p>`:''}
    ${page.candidate_error?`<p class="run-error">${esc(page.candidate_error)}</p>`:''}
    ${page.candidate?`<p class="callout">Unapproved draft${page.candidate.ocr_low_confidence_words!=null?` · ${page.candidate.ocr_low_confidence_words} low-confidence words`:''}. ${esc(page.candidate.warning||'Check this draft against the original before saving.')}${page.candidate.note?`<br>${esc(page.candidate.note)}`:''}</p>`:''}
    <div class="page-review-columns"><div>${page.renderer_available?`<a href="/api/ai/preparation/${encodeURIComponent(page.document_id)}/${page.page}/render" target="_blank" rel="noopener">Open page image at full size</a><img src="/api/ai/preparation/${encodeURIComponent(page.document_id)}/${page.page}/render" alt="Original physical page ${page.page}" data-review-image><p class="small-note" data-render-error hidden>Page rendering failed. Download the original to inspect it; no review has been saved.</p>`:'<p>Page preview requires local Poppler. You can download and inspect the original PDF.</p>'}<a href="/api/ai/documents/current/${encodeURIComponent(page.document_id)}">Download original PDF</a></div>
    <div><label>Page content<select data-review-method aria-label="Page content" ${disabled}><option value="reviewed_text" ${draft.method==='reviewed_text'?'selected':''}>Checked text or transcription</option><option value="nontext" ${draft.method==='nontext'?'selected':''}>No substantive content (for example, a blank page)</option></select></label>
    <label>Complete page text<textarea data-review-text aria-label="Complete page text" rows="20" ${disabled||draft.method==='nontext'?'disabled':''}>${esc(draft.text)}</textarea></label>
    <p class="small-note">Substantive diagrams and tables are not blank pages. OCR can misread columns and cannot reconstruct unlabelled graph values.</p>
    ${!locked?`<div class="inline-actions"><label>OCR language codes<input data-review-language aria-label="OCR language codes" value="${esc(draft.language)}" placeholder="eng or rus+eng" ${busy?'disabled':''}></label><button data-review-ocr ${busy||!page.ocr_available||!page.renderer_available||page.has_candidate?'disabled':''}>${page.has_candidate?'Draft already saved':'Create local OCR draft'}</button></div><p class="small-note">${page.ocr_available?'OCR creates a draft for review; it does not approve the page.':'Local OCR is unavailable: install Tesseract and the required language packs, then restart the preview. Manual transcription is available.'}</p>`:''}
    <label>Inspection note<textarea data-review-note aria-label="Inspection note" rows="3" ${disabled}>${esc(draft.note)}</textarea></label>
    <label class="review-confirm"><input type="checkbox" data-review-confirm ${draft.confirmed?'checked':''} ${disabled}> I checked this content against the original page, including numbers and layout.</label>
    ${locked?'<p class="small-note">This saved review is retained with its source fingerprint.</p>':`<button class="primary" data-review-save ${busy||!draft.confirmed||!draft.note.trim()||draft.method==='reviewed_text'&&!draft.text.trim()?'disabled':''}>${busy?'Working…':'Save checked page'}</button>`}</div></div></section>`;
}

export function runProgress(run,{showError=true}={}){
  const index=runStages.findIndex(([id])=>id===run.stage),done=run.status==='completed';
  const labels={running:'In progress',stopping:'Stopping',stopped:'Stopped',failed:'Needs attention',completed:'Saved'};
  return `<div class="run-heading"><div><span class="run-state ${esc(run.status)}">${labels[run.status]||esc(run.status)}</span><h2>${done?'Your Country Profile is ready':'Country Profile generation'}</h2></div>${active(run)?`<button data-run-action="stop" ${run.status==='stopping'?'disabled':''}>${run.status==='stopping'?'Stopping…':'Stop'}</button>`:''}</div>
    <ol class="run-steps" aria-label="Generation steps">${runStages.map(([id,label],n)=>`<li class="${done||n<index?'done':n===index?'current':''}" ${!done&&n===index?'aria-current="step"':''}><span aria-hidden="true">${done||n<index?'✓':n+1}</span>${label}</li>`).join('')}</ol>
    <div role="status" aria-live="polite"><p class="run-message">${esc(run.message)}${active(run)&&run.total>1?` <span class="muted">· ${run.completed} of ${run.total} complete in this step</span>`:''}</p></div>
    ${showError&&run.error?`<p class="run-error" role="alert">${esc(run.error)}</p>`:''}
    <p class="small-note muted">${esc(selectionSummary(run.selection))}</p>
    <div class="inline-actions">${canResume(run)?'<button class="primary" data-run-action="resume">Resume run</button>':''}${requiresReview(run)?'<button class="primary" data-run-new>Generate with automatic recovery</button>':''}${done?'<button class="primary" data-run-view>View Country Profile</button>':''}${!active(run)?'<button data-run-new>New run</button>':''}</div>
    ${active(run)?'<p class="small-note muted">You can leave this page. Requests can take several minutes. Stop prevents new requests and saves valid results from active requests when they finish.</p>':''}`;
}

export function createGeneration({onSaved,onView,onConnect,onSettings,request=aiRequest}){
  const drafts=new Map();let root=null,code=null,documents=[],sourceAvailabilityUnknown=false,timer,epoch=0;
  const draft=()=>{if(!drafts.has(code))drafts.set(code,{selection:defaultAISelection(),ids:documents.map(d=>d.id),run:null,error:'',busy:false,options:false});return drafts.get(code);};
  function paint(){
    if(!root?.isConnected)return;
    const d=draft(),run=d.run,problem=selectionProblem(d.selection,ai.status),running=active(run),requestingStop=d.pendingAction==='stop',stopping=run?.status==='stopping';
    root.innerHTML=`<section class="paper generation-card" aria-label="Country generation"><div class="run-heading"><div><h2>${running?(requestingStop?'Requesting stop':stopping?'Stopping your profile':'Generating your profile'):run?.status==='completed'?'Update Country Profile':'Generate Country Profile'}</h2><p class="muted">Documents, OCR and evidence checks run automatically. Finished results publish here.</p></div>${running?`<button data-stop ${d.busy||stopping?'disabled':''}>${requestingStop?'Requesting stop…':stopping?'Stopping…':'Stop'}</button>`:`<button class="primary" data-generate ${d.busy||sourceAvailabilityUnknown||!d.ids.length||d.activeCountry?'disabled':''}>${d.busy?'Starting…':run?.status==='completed'?'Update profile':'Generate profile'}</button>`}</div>
      ${running?`<p role="status">${requestingStop?'Requesting a stop. Active requests may need to finish before their results can be saved.':esc(run.message)}${!requestingStop&&run.total>1?` · ${run.completed} / ${run.total}`:''}</p><p class="small-note">${requestingStop||stopping?'Keep the server running while active requests finish and save.':'Progress updates after each request, which may take several minutes. You can leave this page while processing continues.'}</p>`:`<p class="small-note">${sourceAvailabilityUnknown?'Local source availability is unknown':`${d.ids.length} ${d.ids.length===1?'document':'documents'} selected`} · ${esc(selectionSummary(d.selection))}</p>`}
      ${!running&&d.activeCountry?`<p class="callout" role="status">A run for ${esc(d.activeCountry)} is active. Let it finish or stop it on that country's page before generating another profile.</p>`:''}
      ${!running&&problem?`<p class="small-note">${esc(problem)} <button data-connect>Connect AI</button></p>`:''}
      ${!running?`<details class="generation-options" ${d.options?'open':''}><summary>Options</summary><fieldset class="run-documents"><legend>Documents</legend>${documents.map(doc=>`<label class="run-document"><input type="checkbox" data-document="${esc(doc.id)}" ${d.ids.includes(doc.id)?'checked':''}><span>${esc(doc.title)}<small>${doc.pages} ${doc.pages===1?'page':'pages'}</small></span></label>`).join('')}</fieldset>${modelControls(d.selection,'country-model',d.busy)}<button data-settings>Method & output settings</button></details>`:''}
      ${run&&!running?`<details><summary>Last run · ${run.status==='completed'?'Published':run.status==='failed'?'Could not finish':esc(run.status)}</summary><p>${esc(run.message)}</p>${run.error?`<p class="small-note">${esc(requiresReview(run)?'This older run used manual preparation. Generate again to use automatic recovery.':run.error)}</p>`:''}${canResume(run)?`<button data-resume ${d.busy||d.activeCountry?'disabled':''}>Continue saved run</button>`:''}${run.status==='completed'?'<button data-view>Read result</button>':''}</details>`:''}
      ${d.error?`<p class="run-error" role="alert">${esc(d.error)}</p>`:''}</section>`;
    root.querySelector('[data-generate]')?.addEventListener('click',()=>act('start'));
    root.querySelector('[data-stop]')?.addEventListener('click',()=>act('stop'));
    root.querySelector('[data-resume]')?.addEventListener('click',()=>act('resume'));
    root.querySelector('[data-connect]')?.addEventListener('click',onConnect);
    root.querySelector('[data-view]')?.addEventListener('click',()=>onView(code,d.run?.profile_id));
    root.querySelector('[data-settings]')?.addEventListener('click',()=>onSettings?.(code,{document_ids:[...d.ids],selection:{...d.selection}}));
    root.querySelector('.generation-options')?.addEventListener('toggle',e=>{if(e.target.isConnected)d.options=e.target.open;});
    root.querySelectorAll('[data-document]').forEach(input=>input.onchange=()=>{d.touched=true;d.ids=input.checked?[...d.ids,input.dataset.document]:d.ids.filter(id=>id!==input.dataset.document);paint();});
    bindModelControls(root,d.selection,()=>{d.touched=true;paint();},'country-model');
  }
  async function act(action){
    const d=draft(),requestedCode=code;if(d.busy)return;
    if((action==='start'||action==='resume')&&d.activeCountry)return;
    if(action==='stop'&&(!active(d.run)||d.run.status==='stopping'))return;
    if(action==='start'&&(sourceAvailabilityUnknown||!d.ids.length))return;
    if(action==='start'&&selectionProblem(d.selection,ai.status)){onConnect();return;}
    d.busy=true;d.pendingAction=action;d.error='';paint();
    try{d.run=await request(action==='start'?'/country-runs':`/country-runs/${encodeURIComponent(d.run.id)}/${action}`,action==='start'?{country:requestedCode,document_ids:d.ids,...d.selection}:{});}
    catch(error){d.error=error.message;}
    finally{d.busy=false;d.pendingAction=null;if(code===requestedCode){paint();schedule();}}
  }
  function schedule(){clearTimeout(timer);const token=epoch;timer=setTimeout(()=>poll(token),2500);}
  async function poll(token){
    if(token!==epoch||!root?.isConnected)return;
    const requestedCode=code,d=draft();
    try{
      const data=await request(`/countries/${encodeURIComponent(requestedCode)}`);if(token!==epoch)return;
      const previous=d.run,latest=data.runs[0]||null,previousActive=d.activeCountry,previousError=d.error;d.run=latest;d.activeCountry=data.active_country;
      if(!sourceAvailabilityUnknown&&!d.touched&&!d.seeded&&latest){d.ids=latest.document_ids.filter(id=>documents.some(doc=>doc.id===id));d.selection={...latest.selection};d.seeded=true;}
      // A cached rerun can complete entirely between polls. Retry a failed read
      // on the next poll, and mark before the callback because it can remount us.
      const completed=latest?.status==='completed'?`${latest.id}:${latest.profile_id}`:null;
      if(completed&&d.savedRun!==completed){const previousSaved=d.savedRun;d.savedRun=completed;try{await onSaved(requestedCode);}catch(error){d.savedRun=previousSaved;throw error;}}
      if(d.pollError){d.error='';d.pollError=false;}
      if(token!==epoch)return;
      if(JSON.stringify(previous)!==JSON.stringify(latest)||previousActive!==d.activeCountry||previousError!==d.error)paint();
    }catch(error){if(token===epoch){d.error=error.message;d.pollError=true;paint();}}
    finally{if(token===epoch)schedule();}
  }
  return {mount(element,country,docs,options={}){clearTimeout(timer);epoch++;root=element;code=country;documents=docs;sourceAvailabilityUnknown=!!options.sourceAvailabilityUnknown;const d=draft();if(!sourceAvailabilityUnknown)d.ids=!d.touched&&!d.seeded?documents.map(doc=>doc.id):d.ids.filter(id=>documents.some(doc=>doc.id===id));paint();poll(epoch);},
    open(){if(root?.isConnected)act('start');},refresh(){if(root?.isConnected)paint();}};
}
