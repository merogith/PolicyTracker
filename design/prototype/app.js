import {selectionProblem} from '../../integrations/javascript/ai-client.mjs';
import '../../integrations/javascript/dashboard-element.js';
import {compileRequest,describeRequest} from '../../integrations/javascript/operation-request.mjs';
import {viewCards,methodologyPage,showPrompt} from './methodology-view.js';
import {assemblyPanel,showAssembly} from './methodology-view.js';
import {renderAnalysis,renderGroups,renderRequestPreview,toggleSource,uploadSourceFiles} from './analysis-view.js';
import {knowledgePage,configPage,editedFileContent,bindKnowledge} from './knowledge-view.js';
import {settingsPage,settingsFromForm} from './settings-view.js';
import {createGeneration} from './generation-view.js';
import {storedProfile,bindStoredProfile} from './profile-view.js';
import {demoProfile,demoHeader,REPORT_TYPES} from './report-results.js';
import {rememberPosition,restorePosition,restoreFocus,setView,requestDrafts,saveRequestDraft,createProfileCache,applySourceAvailability,countrySourceCount,regionalSourceSummary} from './report-state.js';
import {values,validateView} from '../../integrations/javascript/evidence-model.mjs';
import {operationHistory,openOperation} from './operations-view.js';
import {aiRequest,ai,aiPage,bindAI,initializeAI,defaultAISelection,selectionSummary,bindModelControls} from './ai-view.js';

const main=document.getElementById('main');
main.addEventListener('click',async e=>{const b=e.target.closest('[data-publication]');if(!b)return;b.disabled=true;try{
 const result=await aiRequest('/publication',{id:b.dataset.publication,published:b.dataset.published==='true'});
 if(result.selection){const code=result.selection.country;if(result.selection.synthetic)savedDemo=result;else{savedProfiles.set(code,result);country(code).local_profile_id=result.selection.profile_id;}state.version=null;}
 else await refreshOperations();render();toast(b.dataset.published==='true'?'Published.':'Unpublished. Saved evidence remains in history.');
 }catch(error){b.disabled=false;toast(error.message);}});
const load=async path=>{const r=await fetch(path,{cache:'no-store'});if(!r.ok)throw Error(`Could not load ${path}`);return r.json();};
const [region,catalog,dashboard,input,translation,method,knowledge,methodPack,designExample]=await Promise.all([
  load('../../integrations/fixtures/regional-workspace.json'),load('../../integrations/fixtures/operation-tasks.json'),
  load('../../integrations/fixtures/dashboard.json'),load('../../examples/v2/synthetic-input.json'),load('../../examples/v2/translation.json'),load('../../integrations/fixtures/methodology.json'),load('../../integrations/fixtures/knowledge.json'),load('../../integrations/fixtures/method-pack.json'),load('../../integrations/fixtures/report-experience.json')]).catch(e=>{main.removeAttribute('aria-busy');main.innerHTML='<section class="empty-state"><h1>Workspace could not load</h1><p>Check the local preview server, then reload this page.</p><button id="retry-load">Try again</button></section>';document.getElementById('retry-load').onclick=()=>location.reload();throw e;});
const state={page:'regional',country:null,feature:'brief',query:'',availability:'all',libraryCountry:'all',libraryQuery:'',operationError:'',operationLoading:true,reports:[],operationRuns:[],translationVersions:[],draft:null,methodFocus:null,configDraft:null,configPath:null};
let demoData=null,lastPositionKey=null,routeKey='',restoringRoute=false;
const routeFields=['page','country','feature','version','sampleFeature','demoType','demoState','demoView','methodFocus'];
const savedProfiles=createProfileCache();
const readingProfile=()=>savedProfiles.get(state.country,state.version);
let savedDemo=null,profileServiceError='',inventoryServiceError='';
async function refreshSourceAvailability(){try{applySourceAvailability(region,await aiRequest('/inventory'));inventoryServiceError='';}catch(error){applySourceAvailability(region,null);inventoryServiceError='Local source availability could not be checked. Restart the preview server from this workspace, then check again. '+error.message;}}
await refreshSourceAvailability();
const generation=createGeneration({
 async onSaved(code){const data=await load(`/api/profiles/${encodeURIComponent(code)}`);savedProfiles.set(code,data);const c=country(code);c.local_profile_id=data.selection?.profile_id;c.local_history_count=data.history.length;if(c.local_profile_id)for(const f of region.features)c.features[f.id]='local_checked';if(state.page==='country'&&state.country===code)render();},
 async onView(code,version){state.country=code;state.version=version||null;state.page='country';state.feature='brief';render();await readCountry(code,false,state.version);main.querySelector('.country-nav')?.scrollIntoView({behavior:'smooth'});},
 onConnect(){state.page='ai';render();},
 onSettings(code,options){state.settingsTarget={country:code,...options};state.page='configuration';render();}
});
try {
 const saved=await load('/api/profiles');
 for(const summary of saved.countries){const c=region.countries.find(c=>c.code===summary.country);if(!c)continue;c.local_profile_id=summary.profile_id;c.local_history_count=summary.history_count;if(summary.profile_id)for(const f of region.features)c.features[f.id]='local_checked';}
} catch {profileServiceError='Saved profiles are unavailable. Start or restart the Python preview server to use local profile storage.';}
const esc=value=>String(value??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const human=value=>value.replaceAll('_',' ').replace(/^./,s=>s.toUpperCase());
const country=code=>region.countries.find(c=>c.code===code);
const docs=code=>region.documents.filter(d=>!code||d.country_code===code);
const availableDocs=code=>docs(code).filter(d=>d.local_available);
const sourceStatus=d=>d.local_available?'Original available locally':({missing:'Original not installed',changed:'Original differs from the registered file',invalid:'Original cannot be read safely',unreadable:'Original cannot be read',unknown:'Original availability not checked'}[d.local_status]||'Original unavailable');
function sourceNotice(){const count=availableDocs().length;return inventoryServiceError||!region.source_availability_known?`<p class="callout" role="alert">${esc(inventoryServiceError||'Local source availability could not be checked. Restart the preview server from this workspace, then check again.')} <button type="button" data-refresh-sources>Check local sources</button></p>`:count<region.documents.length?`<p class="callout">${count} of ${region.documents.length} registered originals are available in this workspace. Original PDFs are distributed separately from the application. Add your PDFs in Create analysis, or restore the registered originals and refresh this page. Saved profiles and sample evidence remain readable.</p>`:'';}
const feature=id=>region.features.find(f=>f.id===id);
const statuses={local_checked:'Profile available',not_generated:'Not generated',no_sources:'No sources',ready:'Ready',partial:'Limited',not_applicable:'Not applicable',failed:'Failed'};
const statusText=code=>country(code).local_profile_id?'Profile available':country(code).document_count===null?'Source availability unknown':country(code).document_count?'Not generated':'No documents supplied';
const statusBadge=value=>`<span class="state-label ${value==='no_sources'?'warning':''}">${esc(statuses[value]||value)}</span>`;
const title=(eyebrow,heading,text,action='')=>`<div class="title-row"><div><div class="eyebrow">${eyebrow}</div><h1>${heading}</h1><p class="muted">${text}</p></div>${action}</div>`;
function toast(message){const e=document.getElementById('toast');e.textContent=message;e.hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>e.hidden=true,6000);}
function download(data,name){const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function detail(title,body){document.getElementById('detail-title').textContent=title;document.getElementById('detail-body').innerHTML=body;document.getElementById('detail-dialog').showModal();}
function docDetail(id){const d=region.documents.find(x=>x.id===id);detail(d.title,`<p class="badge neutral">Registered in the supplied inventory</p><dl class="facts"><div><dt>Country folder</dt><dd>${esc(country(d.country_code).name)}</dd></div><div><dt>Declared type</dt><dd>${esc(d.declared_type)} · unverified</dd></div><div><dt>Pages</dt><dd>${d.pages}</dd></div><div><dt>Submission</dt><dd>${esc(d.submission_date||'Not verified')}</dd></div><div><dt>Translations</dt><dd>${state.translationVersions.some(v=>v.document_id===id)?'Saved versions available below':'Not prepared — original retained; English and bilingual copies pending'}</dd></div><div><dt>Text inspection</dt><dd>${d.flagged_pages} low-text pages flagged; not a confirmed failure count</dd></div></dl><p class="callout">Downloads read the registered or archived bytes; reading never starts inference.</p>${d.local_available?`<a href="/api/ai/documents/current/${encodeURIComponent(id)}" download>Download registered original PDF</a>`:`<p class="callout">${esc(sourceStatus(d))}. ${d.local_status==='unknown'?'Restart the preview server and check local sources before generating.':'Add or restore the original before generating a result.'}</p>`}${state.translationVersions.filter(v=>v.document_id===id).map(v=>`<button data-read-translation="${esc(v.version)}" data-kind="${v.kind}" data-country="${v.country||''}">Read saved copy · ${esc(v.created_at)}</button>`).join('')}<button id="translate-this-document" ${d.local_available?'':'disabled'}>Translate documents</button>`);document.querySelectorAll('[data-read-translation]').forEach(b=>b.onclick=async()=>{document.getElementById('detail-dialog').close();try{if(b.dataset.kind==='analysis')await openOperation(b.dataset.readTranslation,detail);else{const data=await load(`/api/profiles/${b.dataset.country}?version=${encodeURIComponent(b.dataset.readTranslation)}`);savedProfiles.set(b.dataset.country,data,b.dataset.readTranslation);state.country=b.dataset.country;state.version=b.dataset.readTranslation;state.feature='documents';state.page='country';render();}}catch(e){toast(e.message);}});document.getElementById('translate-this-document').onclick=()=>{document.getElementById('detail-dialog').close();startAnalysis(null,'translate',[d.id]);};}
function docTable(code){const list=docs(code).filter(d=>state.page!=='library'||`${d.title} ${country(d.country_code).name} ${d.declared_type}`.toLowerCase().includes(state.libraryQuery.toLowerCase()));return list.length?`<div class="table-scroll" tabindex="0" role="region" aria-label="Document inventory"><table class="data-table document-table"><thead><tr><th>Document</th><th>Country</th><th>Type</th><th>Pages</th><th>Translations</th></tr></thead><tbody>${list.map(d=>`<tr><td><button class="table-link" data-doc="${d.id}">${esc(d.title)}</button><small>${esc(sourceStatus(d))}</small></td><td>${esc(country(d.country_code).name)}</td><td>${esc(d.declared_type)}<small>Declared</small></td><td>${d.pages}</td><td><span class="state-label">${state.translationVersions.some(v=>v.document_id===d.id)?'Saved reading copy':'Not prepared'}</span></td></tr>`).join('')}</tbody></table></div>`:'<div class="empty-state"><h2>No documents in this view</h2><p>Change the country or clear your search. Some countries have no supplied documents.</p></div>';}
function regionalRows(){
 const q=state.query.trim().toLocaleLowerCase();
 const list=region.countries.filter(c=>`${c.name} ${c.code}`.toLocaleLowerCase().includes(q)&&(state.availability==='all'||(state.availability==='profiles'?!!c.local_profile_id:state.availability==='missing'?c.document_count===0:!!c.document_count)));
 return list.length?list.map(c=>`<tr><th scope="row"><button class="country-link" data-country="${c.code}">${esc(c.name)}</button></th><td><button class="count-button" data-country="${c.code}" data-feature="documents">${esc(countrySourceCount(c))}</button><small>${[...new Set(docs(c.code).map(d=>d.declared_type))].map(esc).join(' · ')||'No sources supplied'}</small></td><td>${profileServiceError?'Availability unknown':c.local_profile_id?`<button class="table-link" data-country="${c.code}">Read profile →</button>`:c.document_count===null?'Source availability unknown':c.document_count?'Not generated':'Awaiting documents'}</td></tr>`).join(''):'<tr><td colspan="3"><p>No countries match. Clear the search or change availability.</p><button data-clear-countries>Clear filters</button></td></tr>';
}
function regionalPatterns(){
 const profiles=[...savedProfiles.values()].filter(d=>d.profile&&!d.profile.synthetic&&d.profile.published!==false);
 if(!profiles.length)return '';
 const domains=new Map();for(const {profile:p} of profiles)for(const r of p.extraction.records)for(const id of values(p,r,'domain')){const name=p.validation_codebook?.domains?.find(d=>d.id===id)?.name||id;if(!domains.has(name))domains.set(name,new Set());domains.get(name).add(p.country_code);}
 return `<details class="regional-patterns"><summary>Policy themes in ${profiles.length} loaded country profiles</summary><p>Countries with source records in each theme, using each country’s selected published version. Opening a historical version does not change this regional view. Coverage differs; these are not rankings or unique commitment totals. Historical labels keep their saved meanings.</p>${[...domains].sort(([a],[b])=>a.localeCompare(b)).map(([name,codes])=>`<p><strong>${esc(name)}</strong> · ${[...codes].map(code=>`<button class="text-link" data-country="${code}" data-feature="commitments">${esc(country(code)?.name||code)}</button>`).join(', ')}</p>`).join('')}</details>`;
}
function regional(){
 const n=region.countries.filter(c=>c.local_profile_id).length;
 return title('REGIONAL PICTURE','Europe & Central Asia','Climate and disaster policy evidence from national climate commitments (NDCs) and adaptation plans (NAPs).')+`<section class="regional-context" aria-label="Available regional information"><p>${esc(regionalSourceSummary(region))} Inventory ${esc(region.inventory_date)}.</p><p>${profileServiceError?`${esc(profileServiceError)} <button data-retry-profiles>Retry</button>`:n?`${n} country profiles available. Open a country to read its findings and source evidence.`:'Country profiles have not been generated yet. Regional policy findings will appear as profiles become available.'}</p><details><summary>Source coverage</summary><p>Document types and country attribution are supplied metadata awaiting verification. A missing profile or document does not establish policy absence.</p><button id="download-inventory">Export source inventory</button></details></section>${sourceNotice()}${regionalPatterns()}<div class="section-title"><h2>Find a country</h2><button id="design-demo-link" class="text-link">Explore a sample profile</button></div><div class="filter-row regional-filters"><label>Country name or code<input id="country-search" type="search" placeholder="Search countries" value="${esc(state.query)}"></label><label>Show<select id="availability">${[['all','All countries'],['profiles','Profiles available'],['supplied','Documents supplied'],['missing','Missing documents']].map(([id,name])=>`<option value="${id}" ${state.availability===id?'selected':''}>${name}</option>`).join('')}</select></label><button data-clear-countries>Clear filters</button></div><div class="table-scroll" tabindex="0" role="region" aria-label="Countries and available profiles"><table class="data-table coverage-table"><thead><tr><th>Country</th><th>Source documents</th><th>Country profile</th></tr></thead><tbody id="country-rows">${regionalRows()}</tbody></table></div>`;
}

function countryView(){
 const c=country(state.country),saved=savedProfiles.get(c.code,state.version);let content;
 if(saved?.error||profileServiceError)content=`<section class="empty-state" role="alert"><h2>Saved information unavailable</h2><p>${esc(saved?.error||profileServiceError)}</p><button data-retry-country>Try again</button></section>`;
 else if(saved&&(saved.profile||state.feature==='history'&&saved.history.length))content=storedProfile(saved,state.feature);
 else if(c.local_profile_id)content='<p role="status">Loading the saved profile…</p>';
 else if(state.feature==='documents')content=`<h2>Source documents</h2><p class="muted">Registered documents and their local availability appear below. English reading copies appear when prepared.</p>${sourceNotice()}${docTable(c.code)}`;
 else if(state.feature==='history')content=`<section class="empty-state"><h2>No saved versions yet</h2><p>Completed profiles and failed attempts appear here. Your last available profile stays readable if an update fails.</p></section>`;
 else if(c.document_count===null)content=`<section class="empty-state"><h2>Local source availability is unknown</h2><p>${c.registered_document_count} documents are registered for this country. The server could not check their originals, so generation is unavailable until the check succeeds.</p>${sourceNotice()}<button data-country="${c.code}" data-feature="documents">Read the document registry</button></section>`;
 else content=`<section class="empty-state"><h2>${c.document_count?'This profile has not been generated':c.registered_document_count?'Original source documents are not installed':'No source documents supplied'}</h2><p>${c.document_count?`Read the ${c.document_count} source documents now, or select Generate profile above to see findings and commitments.`:c.registered_document_count?'The document registry is present, but its original PDFs are unavailable in this workspace. Add or restore originals before generating a profile.':'A national climate commitment or adaptation plan is needed before a profile can be prepared.'}</p>${c.document_count?`<button data-country="${c.code}" data-feature="documents">Read source documents</button>`:'<button data-nav="library">Browse available documents</button>'}</section>`;
 if(state.version&&saved?.profile)content=`<p class="callout">Reading a specific saved version. <button data-selected-profile>Read the selected country version</button></p>`+content;
 return `<button class="text-link" data-nav="regional">← Regional picture</button>`+title('COUNTRY PROFILE',esc(c.name),`${countrySourceCount(c)}${saved?.profile?' · Saved '+esc(saved.profile.created_at?.slice(0,10)||'date unavailable'):''}`,`<details class="country-actions"><summary>More actions</summary><button data-plan ${c.document_count?'':'disabled'}>${saved?.profile?'Update profile':'Generate profile'}</button><button data-country-analysis ${!c.document_count?'disabled':''}>Create analysis</button><button data-compare ${c.document_count<2?'disabled':''}>Compare documents</button></details>`)+`<nav class="country-nav" aria-label="Country profile">${[['brief','Overview'],['commitments','Policy register'],['documents','Documents & translations'],['history','Version history']].map(([id,label])=>`<button data-country="${c.code}" data-feature="${id}" aria-current="${state.feature===id?'page':'false'}">${label}</button>`).join('')}</nav><div id="country-generation"></div>${content}`;
}

function showGenerationPlan(){
  if(state.page==='country'){generation.open();return;}
  detail('Generate one country',`<p>Open a country in the Regional tracker, then choose <strong>Generate profile</strong>.</p><ol class="generation-stages"><li>Select its documents and your connected model.</li><li>Prepare English text and extract source-linked evidence.</li><li>Link duplicates and flag conflicting commitments.</li><li>Create the Overview, check the results and save both views.</li></ol><p class="muted">Progress is saved locally. Stop after the current request, or resume an interrupted run. Your existing checked profile stays available until a new one passes validation.</p>`);
}
function sample(){
 if(savedDemo?.profile){const view=state.sampleFeature||'brief';return title('SYNTHETIC LOCAL PROFILE','Saved profile example','Invented evidence, stored and checked through the local workflow. Excluded from real country counts.',`<button data-nav="regional">Back to regional dashboard</button>`)+`<nav class="country-nav" aria-label="Saved example profile">${[['brief','Overview'],['commitments','Policy register'],['documents','Documents & translations'],['history','Version history']].map(([id,label])=>`<button data-saved-view="${id}" aria-pressed="${view===id}">${label}</button>`).join('')}</nav>`+storedProfile(savedDemo,view);}
 return title('ILLUSTRATIVE REPORT · SYNTHETIC EVIDENCE','What a completed feature can look like','This invented example is excluded from regional delivery counts.',`<button data-nav="regional">Back to regional dashboard</button>`)+`<section class="paper"><h2>Flood preparedness</h2><p class="brief-lead">The invented source commits to 20 flood early-warning systems by 2030, conditional on international financing.</p><p class="muted">Baseline and financing amount are not stated. Implementation has not been assessed.</p></section><section class="paper" style="margin-top:20px"><h2>Commitments and targets</h2><policy-tracker id="tracker"></policy-tracker></section>`;}
function freshDraft(code){return {step:1,name:'',task:'extract',document_ids:code?availableDocs(code).map(d=>d.id):[],requested_fields:catalog.tasks[0].options.filter(o=>o.default).map(o=>o.id),filters:{domain_ids:[],topic_ids:[],hazards:[],risk_functions:[]},comparison_mode:'documents',groups:[{label:'Earlier edition',document_ids:[]},{label:'Later edition',document_ids:[]}],include_analyst_proposals:false,question:'',instructions:'',uploads:[],model:defaultAISelection()};}
function startAnalysis(code,task='extract',ids){state.draft=freshDraft(code);state.draft.task=task;if(code||ids)state.draft.step=2;state.draft.requested_fields=catalog.tasks.find(t=>t.id===task).options.filter(o=>o.default).map(o=>o.id);if(ids)state.draft.document_ids=ids;state.page='analysis';render();window.scrollTo(0,0);}
const optionList=(items,selected,empty)=>`<option value="">${empty}</option>${items.map(x=>{const id=typeof x==='string'?x:x.id;const label=typeof x==='string'?human(x):x.label||x.name||x.id;return `<option value="${esc(id)}" ${selected===id?'selected':''}>${esc(label)}</option>`;}).join('')}`;
function sourceSelection(){const d=state.draft;const selectedCountries=[...new Set([...(d.sourceCountries||[]),...d.document_ids.map(id=>region.documents.find(x=>x.id===id)?.country_code).filter(Boolean)])];return `${sourceNotice()}<div class="add-source-row"><label>Add a country's documents<select id="source-country"><option value="">Choose country</option>${region.countries.map(c=>`<option value="${c.code}" ${!c.document_count?'disabled':''}>${esc(c.name)} · ${esc(countrySourceCount(c))}${c.document_count===0?' · none available locally':''}</option>`).join('')}</select></label><button type="button" id="add-country">Add documents</button></div>${selectedCountries.map(code=>`<details class="source-group" open><summary>${esc(country(code).name)} · ${d.document_ids.filter(id=>docs(code).some(x=>x.id===id)).length} selected</summary>${docs(code).map(doc=>`<label class="document-choice"><input type="checkbox" data-select-doc="${doc.id}" ${d.document_ids.includes(doc.id)?'checked':''} ${!doc.local_available&&!d.document_ids.includes(doc.id)?'disabled':''}><span>${esc(doc.title)}<small>${esc(doc.declared_type)} · ${doc.pages} pages · ${esc(sourceStatus(doc))}</small></span></label>`).join('')}</details>`).join('')||'<p class="muted">Add one or more countries, then deselect any documents outside your question.</p>'}<details class="support-upload"><summary>Add a PDF</summary><div class="upload-fields"><label>Country<select id="upload-country">${region.countries.map(c=>`<option value="${c.code}" ${(state.country||selectedCountries[0])===c.code?'selected':''}>${esc(c.name)}</option>`).join('')}</select></label><label>Document type<select id="upload-type"><option>NDC</option><option>NAP</option></select></label><label>PDF files<input id="support-files" type="file" accept="application/pdf,.pdf" multiple></label></div><p class="small-note" id="upload-status" role="status">${esc(d.uploadError||'Up to 25 MB per PDF. Added documents are selected automatically.')}</p></details>`;}
function groupsView(){return renderGroups(state.draft,catalog,region);}
function analysis(){return renderAnalysis({d:state.draft,catalog,region,sourceSelection,title});}
function updatePreview(){
 const d=state.draft;let request=null,error='';try{request=compileRequest(d,catalog,region);}catch(e){error=e.message;}
 document.getElementById('request-preview').innerHTML=renderRequestPreview(d,catalog,region,request,error);
 document.getElementById('request-error').textContent=error;document.getElementById('request-error').hidden=!error;
 const busy=!!(d.uploading||d.submitting);document.getElementById('save-request').disabled=!!error||busy;document.getElementById('keep-request').disabled=!!error||busy;document.getElementById('download-analysis-request').disabled=!!error||busy;
 document.getElementById('support-files').disabled=busy;
 document.getElementById('request-success').hidden=true;
}
function reports(){return title('SAVED WORK','Reports & analysis','Prepare a brief, compare policies, extract information, or translate documents.',`<button class="primary" data-new>Create analysis</button>`)+`<details><summary>Saved presets</summary><p class="muted">Saved on this browser · not executed.</p>${requestDrafts().map(r=>`<article class="report-item"><h3>${esc(r.name)}</h3><p>${esc(catalog.tasks.find(t=>t.id===r.draft.task)?.label||r.draft.task)} · ${r.draft.document_ids.length} documents · Saved ${esc(r.saved_at?.slice(0,10)||'')}</p><button data-open-draft="${esc(r.id)}">Reopen request</button></article>`).join('')||'<p>No saved presets yet.</p>'}</details><section class="narrative-section"><div class="section-title"><h2>Analysis results</h2><button id="refresh-operations">Refresh results</button></div>${state.operationError?`<p class="callout" role="alert">${esc(state.operationError)} Use Refresh results to try again.</p>`:''}<div id="operation-history">${state.operationLoading?'<p role="status">Loading saved results…</p>':''}${!state.operationLoading||state.operationRuns.length?operationHistory(state.operationRuns,catalog):''}</div></section><details><summary>Explore sample outputs · invented evidence</summary>${Object.entries(REPORT_TYPES).filter(([k])=>k!=='country').map(([k,v])=>`<button data-demo-type="${k}">${v}</button>`).join('')}</details>`;}

async function refreshOperations(){state.operationLoading=true;if(state.page==='reports')render();try{state.operationRuns=(await aiRequest('/analyses')).runs;state.operationError='';state.translationVersions=(await aiRequest('/translations')).versions;}catch(e){state.operationError='Saved results could not be loaded. '+e.message;}finally{state.operationLoading=false;if(['reports','library'].includes(state.page))render();}}

function render(){
  const priorFocus=document.activeElement,focusId=priorFocus?.id,focusData=priorFocus?.dataset.selectDoc;
  const openPanels=state.page==='analysis'?[...main.querySelectorAll('details[open]')].map(d=>d.querySelector(':scope > summary')?.textContent):[];
  if(lastPositionKey)rememberPosition(lastPositionKey);
  const positionKey=state.page==='country'?[state.page,state.country,state.feature,state.version].join(':'):state.page==='sample'?[state.page,state.sampleFeature].join(':'):state.page==='demonstration'?[state.page,state.demoType,state.demoView,state.demoState].join(':'):state.page;
  lastPositionKey=positionKey;
  document.getElementById('generation-plan').textContent='How to generate';
  document.getElementById('generation-plan').hidden=true;
  document.getElementById('ai-connection-link').hidden=state.page!=='ai';
  document.querySelectorAll('.sidebar [data-nav]').forEach(b=>{const active=state.page==='country'||state.page==='sample'||state.page==='demonstration'?'regional':state.page==='analysis'?'reports':state.page;if(b.dataset.nav===active)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
  document.getElementById('report-count').textContent=state.operationRuns.length;
  document.getElementById('breadcrumb').textContent=state.page==='country'?`Regional picture / ${country(state.country).name}`:({regional:'Regional picture',reports:'Reports & analysis',analysis:'Reports & analysis / Create',help:'Help & getting started',library:'Documents & translations',methodology:'Method & prompts',knowledge:'Knowledge & labels',configuration:'Method & output settings',sample:'Saved illustrative profile',demonstration:'Report demonstrations',integrations:'Integrations'}[state.page]);
  if(state.page==='ai'){document.getElementById('breadcrumb').textContent='Settings / AI connection';main.innerHTML=(state.draft?'<button class="text-link" data-nav="analysis">← Back to analysis request</button>':'')+aiPage();}
  else if(state.page==='link-error')main.innerHTML=`<section class="empty-state"><h1>Linked view unavailable</h1><p>${esc(state.linkError)}</p><button data-nav="regional">Open regional tracker</button></section>`;
  else if(state.page==='help')main.innerHTML=title('PRACTICAL GUIDE','Help & getting started','Choose the question that matches what you need.')+`<section class="help-list"><details open><summary>Where do I begin?</summary><p>Open Regional picture and choose a country. Overview holds the main findings; Policy register lists statements, targets and responsibilities. If a profile is not generated, its original documents are still available.</p><button data-nav="regional">Find a country</button></details><details><summary>How do I find a target or responsibility?</summary><p>Open a country’s Policy register. Search a word, institution or theme, or select Targets or Delivery and support. Open a statement to read the original passage and English translation. Close the evidence panel to return to your filters and reading position.</p></details><details><summary>How do I prepare a tailored report?</summary><p>Choose Create analysis, select a task and documents, then Generate. Reading, OCR recovery, extraction and publication run automatically. Customize output or save a preset when useful. A connected model is required.</p><button data-new>Create analysis</button></details><details><summary>Where are saved work and exports?</summary><p>Reports & analysis holds published results and saved presets. Optional moderation can unpublish a result while preserving its evidence and history. In a country profile, Export offers a readable report, CSV or JSON. Current-view exports retain your filters; the full saved report includes all evidence.</p><button data-nav="reports">Open saved work</button></details><details><summary>What do missing information and failed updates mean?</summary><p>Not generated means there is no saved profile yet. Unavailable means saved information could not be read; retry after checking the local server. No matches means the current filters found no records. None of these establishes that a policy is absent. An unsuccessful update leaves the previous saved profile available.</p></details><details><summary>Can I check labels, methods and earlier versions?</summary><p>Evidence details show classifications and the definitions saved with that version. Version history opens earlier profiles. Method & prompts and Knowledge & labels describe the current configuration; they do not replace a historical profile’s archived method.</p><button data-nav="knowledge">Find a definition</button><button data-nav="methodology">Read the method</button></details></section>`;
  else if(state.page==='regional') main.innerHTML=regional();
  else if(state.page==='country') main.innerHTML=countryView();
  else if(state.page==='analysis') main.innerHTML=analysis();
  else if(state.page==='reports') main.innerHTML=reports();
  else if(state.page==='sample') main.innerHTML=sample();
  else if(state.page==='demonstration'){const type=state.demoType||'country',variant=state.demoState||'current',view=type==='translate'?'documents':state.demoView||'brief';const profile=demoProfile(designExample,type,variant);demoData={profile,selection:{stale_sources:variant==='outdated'},history:[]};main.innerHTML=demoHeader(type,variant,view)+storedProfile(demoData,view);main.append(main.querySelector('.demo-controls'));}
  else if(state.page==='methodology') main.innerHTML=methodologyPage(method,state.methodFocus)+assemblyPanel(method);
  else if(state.page==='knowledge')main.innerHTML=knowledgePage(knowledge);
  else if(state.page==='configuration'){main.innerHTML=settingsPage(state.settings,catalog.facets.topics,region.countries,state.settingsTarget)+(state.configDraft?`<details class="paper"><summary>Advanced method editor</summary>${configPage(state.configDraft)}<button id="apply-method" class="primary">Apply method changes</button></details>`:'');}
  else if(state.page==='library') main.innerHTML=title('DOCUMENT LIBRARY','Documents & translations','Find original documents and any saved English reading copies.',`<button data-translate>Translate documents</button>`)+`<div class="filter-row"><label>Country<select id="library-country"><option value="all">All countries · ${region.documents.length} documents</option>${region.countries.map(c=>`<option value="${c.code}" ${state.libraryCountry===c.code?'selected':''}>${esc(c.name)} · ${esc(countrySourceCount(c))}</option>`).join('')}</select></label><label>Find a document<input type="search" id="library-search" placeholder="Title, country or type" value="${esc(state.libraryQuery)}"></label><button id="clear-library">Clear filters</button></div>${sourceNotice()}<div id="library-results">${docTable(state.libraryCountry==='all'?null:state.libraryCountry)}</div>`;
  else main.innerHTML=title('REUSE THE EVIDENCE','Integrations','Use the same country bundles in another website or operational tool.')+`<div class="integration-grid"><section class="paper"><h2>Structured exports</h2><p>JSON inventory downloads work here. Saved local profiles support JSON and register CSV downloads with nested details and bilingual evidence. The report reader also exports filtered evidence and readable HTML with version, definitions and limitations.</p><button id="download-inventory">Download inventory metadata</button></section><section class="paper"><h2>Website components</h2><p>A data-only tracker and authorized evidence viewer can fit into an existing website.</p><button id="sample-link">View illustrative tracker</button></section><section class="paper"><h2>API and AI connector</h2><p>Read regional status, country reports and sources. Explicit analysis requests use separate permissions.</p><p class="muted">Contracts prepared; services not deployed.</p></section></div>`;
  syncRoute();bind();if(state.page==='analysis')updatePreview();
  restorePosition(positionKey);
  if(state.page==='analysis')main.querySelectorAll('details').forEach(d=>{if(openPanels.includes(d.querySelector(':scope > summary')?.textContent))d.open=true;});
  restoreFocus(main,focusId,focusData);

}
function bind(){
 main.querySelectorAll('[data-refresh-sources]').forEach(b=>b.onclick=async()=>{b.disabled=true;await refreshSourceAvailability();render();});
 main.querySelectorAll('[data-open-draft]').forEach(b=>b.onclick=()=>{const r=requestDrafts().find(x=>x.id===b.dataset.openDraft);state.draft={...r.draft,id:r.id,name:r.name,step:3};state.page='analysis';render();});
 main.querySelectorAll('[data-clear-countries]').forEach(b=>b.onclick=()=>{state.query='';state.availability='all';render();document.getElementById('country-search')?.focus();});
 main.querySelector('[data-retry-country]')?.addEventListener('click',()=>readCountry(state.country,true,state.version));
 main.querySelector('[data-selected-profile]')?.addEventListener('click',()=>{state.version=null;render();readCountry(state.country,true);});
 main.querySelector('[data-retry-profiles]')?.addEventListener('click',()=>location.reload());

 document.getElementById('refresh-operations')?.addEventListener('click',refreshOperations);
 main.querySelectorAll('[data-operation]').forEach(b=>b.onclick=()=>openOperation(b.dataset.operation,detail,refreshOperations).catch(e=>toast(e.message)));
 main.querySelectorAll('[data-operation-request]').forEach(b=>b.onclick=()=>download(state.operationRuns.find(r=>r.id===b.dataset.operationRequest).operation,'analysis-request.json'));
 main.querySelectorAll('[data-operation-action]').forEach(b=>b.onclick=async()=>{b.disabled=true;try{await aiRequest(`/country-runs/${encodeURIComponent(b.dataset.id)}/${b.dataset.operationAction}`,{});await refreshOperations();}catch(e){toast(e.message);b.disabled=false;}});
 main.querySelectorAll('[data-history-read],[data-history-pin],[data-history-unpin]').forEach(b=>b.onclick=async()=>{try{const data=state.page==='sample'?savedDemo:readingProfile(),code=data.selection.country,synthetic=!!data.selection.synthetic;if(b.hasAttribute('data-history-read')){const loaded=await load(`/api/profiles/${code}?version=${encodeURIComponent(b.dataset.historyRead)}${synthetic?'&synthetic=1':''}`);if(synthetic){savedDemo=loaded;state.sampleFeature='brief';}else{savedProfiles.set(code,loaded,b.dataset.historyRead);state.version=b.dataset.historyRead;state.feature='brief';}}else{await aiRequest('/profile-selection/'+code,{profile_id:b.dataset.historyPin||null,revision:data.selection.revision,synthetic});const loaded=await load(`/api/profiles/${code}${synthetic?'?synthetic=1':''}`);if(synthetic)savedDemo=loaded;else savedProfiles.set(code,loaded);state.version=null;}render();}catch(e){toast(e.message);}});

 if(state.page==='country')generation.mount(document.getElementById('country-generation'),state.country,availableDocs(state.country),{sourceAvailabilityUnknown:country(state.country).document_count===null});
 main.querySelectorAll('[data-saved-view]').forEach(b=>b.onclick=()=>{if(state.page==='sample')state.sampleFeature=b.dataset.savedView;else state.feature=b.dataset.savedView;render();});
 main.querySelector('[data-profile-json]')?.addEventListener('click',()=>{const p=(state.page==='sample'?savedDemo:readingProfile())?.profile;if(p)download(p,`${p.country_code}-${p.id}.json`);});
 bindStoredProfile(main,state.page==='demonstration'?demoData:state.page==='sample'?savedDemo:readingProfile(),{onExplore(){if(state.page==='demonstration')state.demoView='commitments';else if(state.page==='sample')state.sampleFeature='commitments';else state.feature='commitments';render();},async onCopyLink(v){
   const current=(state.page==='demonstration'?demoData:state.page==='sample'?savedDemo:readingProfile())?.profile;
   if(!current)return;
   const url=new URL(location.href);url.search='';url.hash='';
   if(state.page==='sample'&&savedDemo?.profile){url.searchParams.set('country',savedDemo.profile.country_code);url.searchParams.set('savedExample','1');url.searchParams.set('tab',state.sampleFeature||'brief');url.searchParams.set('profile',savedDemo.profile.id);}
 if(state.page==='demonstration'){url.searchParams.set('example',state.demoType||'country');url.searchParams.set('case',state.demoState||'current');url.searchParams.set('tab',state.demoView||'brief');}
   else{url.searchParams.set('country',current.country_code);if(current.synthetic)url.searchParams.set('savedExample','1');url.searchParams.set('tab',state.page==='sample'?state.sampleFeature||'brief':state.feature);}
   url.searchParams.set('profile',current.id);url.searchParams.set('view',JSON.stringify(v));
   try{await navigator.clipboard.writeText(url.href);toast('Local view link copied. It works only where this local server and version are accessible; it grants no document access.');}
   catch{detail('Local view link',`<p>This local-server link preserves the version and presentation. It grants no access.</p><textarea readonly rows=5>${esc(url.href)}</textarea>`);}
 }});
 document.getElementById('design-demo-link')?.addEventListener('click',()=>{state.page='demonstration';state.demoType='country';render();});
 document.getElementById('saved-example')?.addEventListener('click',openSavedExample);
 main.querySelectorAll('[data-demo-type]').forEach(b=>b.onclick=()=>{state.page='demonstration';state.demoType=b.dataset.demoType;state.demoView='brief';render();});
 main.querySelectorAll('[data-demo-view]').forEach(b=>b.onclick=()=>{state.demoView=b.dataset.demoView;render();});
 document.getElementById('demo-type')?.addEventListener('change',e=>{state.demoType=e.target.value;state.demoView='brief';render();});
 document.getElementById('demo-state')?.addEventListener('change',e=>{state.demoState=e.target.value;render();});
 if(state.page==='ai')bindAI(main);
 document.getElementById('inspect-assembly')?.addEventListener('click',()=>showAssembly(method,document.getElementById('method-assembly').value,detail));
 main.querySelectorAll('[data-translate]').forEach(b=>b.onclick=()=>startAnalysis(state.page==='country'?state.country:state.libraryCountry==='all'?null:state.libraryCountry,'translate'));
 main.querySelectorAll('[data-compare]').forEach(b=>b.onclick=()=>startAnalysis(state.country,'compare'));
 main.querySelectorAll('[data-task-method]').forEach(b=>b.onclick=()=>{const t=catalog.tasks.find(t=>t.id===b.dataset.taskMethod);showPrompt(method,t.supplement,detail);});
 main.querySelector('[data-download-knowledge]')?.addEventListener('click',()=>download(knowledge,'knowledge-codebook.json'));
 if(state.page==='knowledge')bindKnowledge(main,knowledge);
 document.getElementById('prompt-query')?.addEventListener('input',e=>{let n=0;const q=e.target.value.trim().toLowerCase();main.querySelectorAll('[data-prompt-search]').forEach(p=>{p.hidden=!p.dataset.promptSearch.includes(q);if(!p.hidden)n++;});document.getElementById('prompt-search-count').textContent=n?`${n} prompts match`:'No prompts match. Try another word.';});
 if(state.page==='configuration'){bindSettings();if(state.configDraft)bindConfiguration();}
  main.querySelectorAll('[data-method]').forEach(b=>b.addEventListener('click',()=>{state.methodFocus=b.dataset.method||null;state.page='methodology';render();main.focus();window.scrollTo(0,0);}));
  main.querySelectorAll('[data-prompt]').forEach(b=>b.addEventListener('click',()=>showPrompt(method,b.dataset.prompt,detail)));
  main.querySelector('[data-download-method]')?.addEventListener('click',()=>download(method,'configured-method-and-prompts.json'));
  main.querySelectorAll('[data-nav]').forEach(b=>b.addEventListener('click',()=>{state.page=b.dataset.nav;if(state.page==='methodology')state.methodFocus=null;render();}));
  main.querySelectorAll('[data-new]').forEach(b=>b.addEventListener('click',()=>startAnalysis()));
  main.querySelectorAll('[data-doc]').forEach(b=>b.addEventListener('click',()=>docDetail(b.dataset.doc)));
  bindCountryLinks();
  main.querySelectorAll('[data-plan]').forEach(b=>b.addEventListener('click',showGenerationPlan));
  document.getElementById('country-search')?.addEventListener('input',e=>{state.query=e.target.value;document.getElementById('country-rows').innerHTML=regionalRows();bindCountryLinks();main.querySelector('[data-clear-countries]')?.addEventListener('click',()=>{state.query='';state.availability='all';render();});});
  document.getElementById('availability')?.addEventListener('change',e=>{state.availability=e.target.value;render();});
  document.getElementById('clear-library')?.addEventListener('click',()=>{state.libraryCountry='all';state.libraryQuery='';render();});
  document.getElementById('library-search')?.addEventListener('input',e=>{state.libraryQuery=e.target.value;document.getElementById('library-results').innerHTML=docTable(state.libraryCountry==='all'?null:state.libraryCountry);main.querySelectorAll('[data-doc]').forEach(b=>b.onclick=()=>docDetail(b.dataset.doc));});
  document.getElementById('library-country')?.addEventListener('change',e=>{state.libraryCountry=e.target.value;render();});
  document.getElementById('download-inventory')?.addEventListener('click',()=>download(region,'regional-inventory.json'));
  document.getElementById('sample-link')?.addEventListener('click',openSavedExample);
  main.querySelector('[data-country-analysis]')?.addEventListener('click',()=>startAnalysis(state.country));
  const tracker=document.getElementById('tracker');if(tracker){tracker.data=dashboard;tracker.addEventListener('evidenceopen',()=>document.getElementById('evidence-dialog').showModal());}
  main.querySelectorAll('[data-download-request]').forEach(b=>b.addEventListener('click',()=>download(state.reports[Number(b.dataset.downloadRequest)],'analysis-request.json')));
  main.querySelectorAll('[data-request]').forEach(b=>b.addEventListener('click',()=>{const r=state.reports[Number(b.dataset.request)];const s=describeRequest(r,catalog);detail(s.task,`<p class="badge neutral">Request only · not run</p><p>${esc(s.groups.join(' / '))}</p><ul>${s.effects.map(t=>`<li>${esc(t)}</li>`).join('')}</ul><details><summary>Structured request</summary><pre class="code-sample">${esc(JSON.stringify(r,null,2))}</pre></details>`);}));
  if(state.page==='analysis')bindAnalysis();
}
async function readCountry(code,force=false,version=null){
 const cached=savedProfiles.get(code,version);if(!force&&cached&&!cached.error)return;
 try{savedProfiles.set(code,await load(`/api/profiles/${encodeURIComponent(code)}${version?'?version='+encodeURIComponent(version):''}`),version);profileServiceError='';}
 catch{savedProfiles.set(code,{error:'Could not read the saved profile. Check that the local preview server is running, then try again.'},version);}
 if(state.page==='country'&&state.country===code&&(state.version||null)===(version||null))render();
}
function bindCountryLinks(){main.querySelectorAll('[data-country]').forEach(b=>{b.onclick=()=>{if(state.page!=='country'||state.country!==b.dataset.country)state.version=null;state.country=b.dataset.country;state.feature=b.dataset.feature||'brief';state.page='country';render();readCountry(state.country,false,state.version);};});}

function bindAnalysis(){const d=state.draft;
 main.querySelectorAll('[data-request-step]').forEach(b=>b.onclick=()=>{d.step=Number(b.dataset.requestStep);render();main.focus();window.scrollTo(0,0);});
 document.getElementById('request-name')?.addEventListener('input',e=>d.name=e.target.value);
 document.getElementById('keep-request')?.addEventListener('click',()=>{try{compileRequest(d,catalog,region);const saved=saveRequestDraft(d,document.getElementById('request-name').value,d.id);d.id=saved.item.id;d.name=saved.item.name;const success=document.getElementById('request-success');success.hidden=false;success.textContent=saved.persisted?'Request saved on this browser. Reopen it from Reports & analysis. No analysis has run.':'Request kept for this tab only because browser storage is unavailable. Download a copy to keep it.';}catch(e){toast(e.message);}});

  main.querySelectorAll('input[name="task"]').forEach(e=>e.addEventListener('change',()=>{d.task=e.value;d.question='';d.instructions='';d.include_analyst_proposals=false;d.comparison_mode='documents';d.groups=[{label:'Earlier edition',document_ids:[]},{label:'Later edition',document_ids:[]}];d.requested_fields=catalog.tasks.find(t=>t.id===d.task).options.filter(o=>o.default).map(o=>o.id);if(d.task==='translate')d.filters={domain_ids:[],topic_ids:[],hazards:[],risk_functions:[]};render();}));
  document.getElementById('add-country').addEventListener('click',()=>{const code=document.getElementById('source-country').value;if(!code){toast('Choose a country to add.');return;}d.sourceCountries=[...new Set([...(d.sourceCountries||[]),code])];d.document_ids=[...new Set([...d.document_ids,...availableDocs(code).map(x=>x.id)])];render();});
  main.querySelectorAll('[data-select-doc]').forEach(e=>e.addEventListener('change',()=>{toggleSource(d,e.dataset.selectDoc,e.checked,region.documents);render();}));
  main.querySelectorAll('[data-output]').forEach(e=>e.addEventListener('change',()=>{d.requested_fields=e.checked?[...new Set([...d.requested_fields,e.dataset.output])]:d.requested_fields.filter(id=>id!==e.dataset.output);updatePreview();}));
  main.querySelectorAll('[data-analysis-filter]').forEach(e=>e.addEventListener('change',()=>{
    const key=e.dataset.analysisFilter;
    d.filters[key]=[...main.querySelectorAll(`[data-analysis-filter="${key}"]:checked`)].map(input=>input.value);
    main.querySelector(`[data-filter-count="${key}"]`).textContent=d.filters[key].length?`${d.filters[key].length} selected`:'All';
    updatePreview();
  }));
  document.getElementById('clear-analysis-filters')?.addEventListener('click',()=>{
    for(const key of Object.keys(d.filters))d.filters[key]=[];
    main.querySelectorAll('[data-analysis-filter]').forEach(e=>{e.checked=false;});
    main.querySelectorAll('[data-filter-count]').forEach(e=>{e.textContent='All';});
    updatePreview();
  });
  document.getElementById('comparison-mode')?.addEventListener('change',e=>{d.comparison_mode=e.target.value;const labels=catalog.comparison_modes.find(m=>m.id===d.comparison_mode).labels||['Group A','Group B'];d.groups=labels.map(label=>({label,document_ids:[]}));render();});
  main.querySelectorAll('[data-group-label]').forEach(e=>e.addEventListener('change',()=>{d.groups[Number(e.dataset.groupLabel)].label=e.value;render();}));
  main.querySelectorAll('[data-assign]').forEach(e=>e.addEventListener('change',()=>{d.groups.forEach(g=>g.document_ids=g.document_ids.filter(id=>id!==e.dataset.assign));if(e.value!=='')d.groups[Number(e.value)].document_ids.push(e.dataset.assign);updatePreview();}));
  document.getElementById('add-group')?.addEventListener('click',()=>{d.groups.push({label:`Group ${d.groups.length+1}`,document_ids:[]});render();});
  document.getElementById('policy-question')?.addEventListener('input',e=>{d.question=e.target.value;updatePreview();});
  document.getElementById('extra-instructions').addEventListener('input',e=>{d.instructions=e.target.value;updatePreview();});
  document.getElementById('proposals')?.addEventListener('change',e=>{d.include_analyst_proposals=e.target.checked;updatePreview();});
  bindModelControls(main,d.model,()=>render(),'analysis-ai');
  document.getElementById('support-files').addEventListener('change',async e=>{
    const status=document.getElementById('upload-status'),files=[...e.target.files],country=document.getElementById('upload-country').value,type=document.getElementById('upload-type').value;
    if(d.uploading||d.submitting||!files.length)return;d.uploading=true;updatePreview();
    try{await uploadSourceFiles(files,{
      readFile:file=>new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(Error('Could not read the PDF'));reader.readAsDataURL(file);}),
      register:(file,base64)=>aiRequest('/documents/register',{country,type,filename:file.name,title:file.name.replace(/\.pdf$/i,''),base64}),
      onProgress:name=>{status.textContent='Adding '+name+'…';},
      onRegistered:added=>{d.document_ids=[...new Set([...d.document_ids,added.document.document_id])];},
      refresh:async()=>{const profiles=new Map(region.countries.map(c=>[c.code,{local_profile_id:c.local_profile_id,local_history_count:c.local_history_count}]));Object.assign(region,await load('../../integrations/fixtures/regional-workspace.json'));for(const c of region.countries)Object.assign(c,profiles.get(c.code)||{});await refreshSourceAvailability();}
    });d.uploads=[];d.uploadError='';toast('Documents added and selected.');}
    catch(error){d.uploadError=error.message;toast(error.message);}
    finally{d.uploading=false;if(state.page==='analysis'&&state.draft===d)render();}
  });
  main.querySelector('[data-output-settings]')?.addEventListener('click',()=>{state.settingsTarget={draft:structuredClone(d)};state.page='configuration';render();});
  document.getElementById('download-analysis-request')?.addEventListener('click',()=>{try{download(compileRequest(d,catalog,region),'analysis-request.json');}catch(e){toast(e.message);}});
  document.getElementById('analysis-form').addEventListener('submit',async e=>{e.preventDefault();if(d.submitting||d.uploading)return;if(selectionProblem(d.model,ai.status)){state.page='ai';render();return;}d.submitting=true;updatePreview();try{const request=compileRequest(d,catalog,region);await aiRequest('/analyses',request);if(state.page==='analysis'&&state.draft===d)state.page='reports';else toast('Analysis started. Open Reports & analysis to follow its progress.');await refreshOperations();}catch(err){toast(err.message);}finally{d.submitting=false;if(state.page==='analysis'&&state.draft===d)updatePreview();}});
}
document.querySelector('[data-header-new]').onclick=()=>startAnalysis();
document.getElementById('navigation-toggle').onclick=()=>{const b=document.getElementById('navigation-toggle');b.setAttribute('aria-expanded',b.getAttribute('aria-expanded')!=='true');};
document.querySelectorAll('.sidebar [data-nav]').forEach(b=>b.addEventListener('click',()=>{document.getElementById('navigation-toggle').setAttribute('aria-expanded','false');state.page=b.dataset.nav;if(state.page==='methodology')state.methodFocus=null;render();}));
document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>document.getElementById(b.dataset.close).close()));
document.getElementById('generation-plan').addEventListener('click',showGenerationPlan);
document.getElementById('english-quote').textContent=translation.segments.find(s=>s.segment_id==='s-1').english_text;
document.getElementById('original-quote').textContent=input.source_segments['s-1'];
await restoreLinkedView();
render();
main.removeAttribute('aria-busy');
document.querySelectorAll('[data-startup]').forEach(button=>{button.disabled=false;button.removeAttribute('data-startup');});
document.getElementById('ai-connection-link').addEventListener('click',()=>{state.page='ai';render();main.focus();});
initializeAI(()=>{const link=document.getElementById('ai-connection-link');const connected=ai.status?.chatgpt.connected||ai.status?.api.connected;link.textContent=connected?'AI connected':'Connect AI';link.classList.toggle('connected',!!connected);if(state.page==='ai'||state.page==='analysis')render();else if(state.page==='country')generation.refresh();});

async function openSavedExample(){
 state.page='sample';render();
 if(profileServiceError)return;
 try{savedDemo=await load('/api/profiles/KAZ?synthetic=1');if(state.page==='sample')render();}
 catch{toast('The saved example could not be read. The illustrative fixture is still available.');}
}

async function refreshMethodAssets(){const paths=['../../integrations/fixtures/operation-tasks.json','../../integrations/fixtures/methodology.json','../../integrations/fixtures/knowledge.json'];const fresh=await Promise.all(paths.map(load));[catalog,method,knowledge].forEach((target,i)=>{for(const key of Object.keys(target))delete target[key];Object.assign(target,fresh[i]);});}
async function loadSettings(){
 state.settingsLoading=true;
 try{state.settings=await aiRequest('/settings');Object.assign(methodPack,await aiRequest('/method'));state.configDraft=structuredClone(methodPack);}
 catch(error){state.settingsError=error.message;}
 finally{state.settingsLoading=false;if(state.page==='configuration')render();}
}
function bindSettings(){
 if(!state.settings){if(!state.settingsLoading&&!state.settingsError)loadSettings();if(state.settingsError)main.innerHTML=`<h1>Settings unavailable</h1><p>${esc(state.settingsError)}</p><button id="retry-settings">Try again</button>`;document.getElementById('retry-settings')?.addEventListener('click',()=>{state.settingsError='';loadSettings();});return;}
 const form=document.getElementById('settings-form');
 const save=async(rerun=false,restore=null)=>{
   const status=document.getElementById('settings-status'),country=form.elements.rerun_country.value;
   form.querySelectorAll('button').forEach(b=>b.disabled=true);status.textContent='Saving settings…';
   try{
     state.settings=await aiRequest('/settings',{revision:state.settings.revision,...(restore?{restore}:{settings:settingsFromForm(form,state.settings.settings)})});
     Object.assign(methodPack,await aiRequest('/method'));state.configDraft=structuredClone(methodPack);await refreshMethodAssets();
     if(rerun){status.textContent='Settings saved. Starting…';
       if(state.settingsTarget?.draft){await aiRequest('/analyses',compileRequest(state.settingsTarget.draft,catalog,region));state.page='reports';await refreshOperations();}
       else{await aiRequest('/country-runs',{country,document_ids:state.settingsTarget?.country===country?state.settingsTarget.document_ids||availableDocs(country).map(d=>d.id):availableDocs(country).map(d=>d.id),...(state.settingsTarget?.selection||defaultAISelection())});state.country=country;state.feature='brief';state.page='country';render();}
     }else{render();document.getElementById('settings-status').textContent='Saved. Future runs will use these settings.';}
   }catch(error){status.textContent=error.message;form.querySelectorAll('button').forEach(b=>b.disabled=false);}
 };
 form.onsubmit=e=>{e.preventDefault();save();};document.getElementById('settings-rerun').onclick=()=>save(true);
 form.querySelectorAll('[data-restore-settings]').forEach(b=>b.onclick=()=>save(false,b.dataset.restoreSettings));
}

function bindConfiguration(){
 const select=document.getElementById('config-file'),editor=document.getElementById('config-content'),status=document.getElementById('config-status');
 const refresh=()=>{state.configPath=select.value;editor.value=state.configDraft.files.find(f=>f.path===select.value).content;document.getElementById('config-file-help').textContent=select.value.endsWith('.md')?'Markdown instructions: edit wording directly.':'JSON configuration: stable IDs, definitions and version numbers must stay consistent.';check();};
 const check=()=>{
  const changed=state.configDraft.files.filter(f=>f.content!==methodPack.files.find(base=>base.path===f.path)?.content).length;
  try{
    for(const f of state.configDraft.files){if(!f.content.trim())throw Error(f.path+': file is blank');if(f.path.endsWith('.json'))JSON.parse(f.content);}
    status.textContent=changed?`Draft · ${changed} changed file${changed===1?'':'s'} · not applied. Syntax valid; run local cross-file validation before applying.`:'Current generated configuration · no draft changes. This is not a historical run record.';
    document.getElementById('export-config').disabled=false;
  }catch(e){status.textContent='Draft has an error: '+e.message;document.getElementById('export-config').disabled=true;}
 };
 select.value=state.configPath||state.configDraft.files[0].path;select.onchange=refresh;
 editor.oninput=()=>{const original=methodPack.files.find(f=>f.path===select.value).content;state.configDraft.files.find(f=>f.path===select.value).content=editedFileContent(original,editor.value);check();};
 document.getElementById('apply-method')?.addEventListener('click',async e=>{e.target.disabled=true;try{await aiRequest('/method',state.configDraft);Object.assign(methodPack,await aiRequest('/method'));state.configDraft=structuredClone(methodPack);state.settings=await aiRequest('/settings');await refreshMethodAssets();render();toast('Method saved. New runs will use it.');}catch(error){status.textContent=error.message;e.target.disabled=false;}});
 document.getElementById('export-config').onclick=()=>{download(state.configDraft,'method-pack-draft.json');status.textContent='Download requested · not applied. Save the file, then validate and apply it locally.';};refresh();
}

async function restoreLinkedView(){
 const q=new URLSearchParams(location.search);if(!q.has('profile')){
   const page=q.get('page');if(page==='analysis'||page==='sample')state.page='reports';if(['regional','reports','library','methodology','knowledge','configuration','ai','help','integrations'].includes(page))state.page=page;
   if(q.get('country')&&country(q.get('country'))){state.page='country';state.country=q.get('country');state.feature=['brief','commitments','documents','history'].includes(q.get('tab'))?q.get('tab'):'brief';try{savedProfiles.set(state.country,await load('/api/profiles/'+state.country));}catch{savedProfiles.set(state.country,{error:'Saved information is unavailable. Try again.'});}}
   return;
 }
 try{
   const tab=q.get('tab');if(!['brief','commitments','documents','history'].includes(tab))throw Error('The linked view is unsupported.');
   let data;
   if(q.has('example')){
     const type=q.get('example'),variant=q.get('case');if(!Object.hasOwn(REPORT_TYPES,type)||!['current','earlier','outdated','failed','empty'].includes(variant))throw Error('The linked demonstration is unavailable.');
     state.page='demonstration';state.demoType=type;state.demoState=variant;state.demoView=tab;data={profile:demoProfile(designExample,type,variant)};
   }else{
     const code=q.get('country');if(!country(code))throw Error('The linked country is unavailable.');
     const synthetic=q.get('savedExample')==='1';data=await load(`/api/profiles/${encodeURIComponent(code)}?version=${encodeURIComponent(q.get('profile'))}${synthetic?'&synthetic=1':''}`);
     if(synthetic){savedDemo=data;state.page='sample';state.sampleFeature=tab;}else{savedProfiles.set(code,data,q.get('profile'));state.page='country';state.country=code;state.feature=tab;state.version=q.get('profile');}
   }
   if(data.profile?.id!==q.get('profile'))throw Error('The linked version is not available through this reader. A newer version has not been substituted.');
   if(q.has('view')){const v=JSON.parse(q.get('view'));if(v.profileId!==data.profile.id)throw Error('The linked preferences refer to another version.');const errors=validateView(data.profile,v);if(errors.length)throw Error(errors.join(' '));setView(data.profile,v);}
 }catch(e){state.page='link-error';state.linkError=e.message;}
}

refreshOperations();
Promise.all(region.countries.filter(c=>c.local_profile_id).map(c=>readCountry(c.code))).then(()=>{if(state.page==='regional')render();});
setInterval(()=>{if(state.page==='reports'&&state.operationRuns.some(r=>['running','stopping'].includes(r.status)))refreshOperations();},2500);

function syncRoute(){
 const route={...Object.fromEntries(routeFields.map(k=>[k,state[k]??null])),savedProfile:state.page==='sample'&&savedDemo?.profile?{country:savedDemo.profile.country_code,id:savedDemo.profile.id}:null},key=JSON.stringify(route);
 if(key===routeKey)return;
 const changed=!!routeKey;routeKey=key;const url=new URL(location.href);url.search='';
 url.searchParams.set('page',state.page);
 if(state.page==='country'){url.searchParams.set('country',state.country);url.searchParams.set('tab',state.feature);if(state.version)url.searchParams.set('profile',state.version);}
 if(state.page==='sample'&&savedDemo?.profile){url.searchParams.set('country',savedDemo.profile.country_code);url.searchParams.set('savedExample','1');url.searchParams.set('tab',state.sampleFeature||'brief');url.searchParams.set('profile',savedDemo.profile.id);}
 if(state.page==='demonstration'){url.searchParams.set('example',state.demoType||'country');url.searchParams.set('case',state.demoState||'current');url.searchParams.set('tab',state.demoView||'brief');url.searchParams.set('profile',demoProfile(designExample,state.demoType||'country',state.demoState||'current').id);}
 if(!restoringRoute)history[changed?'pushState':'replaceState'](route,'',url);
 document.title=(document.getElementById('breadcrumb').textContent||'PolicyTracker')+' · PolicyTracker';
 if(changed&&!restoringRoute)main.focus({preventScroll:true});
}
window.addEventListener('popstate',async event=>{
 if(!event.state)return;restoringRoute=true;Object.assign(state,event.state);
 if(state.page==='analysis'&&!state.draft)state.page='reports';
 if(state.page==='country'&&state.country)await readCountry(state.country,true,state.version);
 if(state.page==='sample'&&event.state.savedProfile){try{const selected=event.state.savedProfile;savedDemo=await load(`/api/profiles/${encodeURIComponent(selected.country)}?synthetic=1&version=${encodeURIComponent(selected.id)}`);}catch{state.page='link-error';state.linkError='Could not read this saved example version. A newer version has not been substituted.';}}
 render();restoringRoute=false;
});
