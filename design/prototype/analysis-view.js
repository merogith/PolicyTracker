import {selectionProblem} from '../../integrations/javascript/ai-client.mjs';
import {modelControls,selectionSummary,ai} from './ai-view.js';
const esc=v=>String(v??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const human=v=>v.replaceAll('_',' ').replace(/^./,s=>s.toUpperCase());

function subjectFilters(d,catalog){
 return [['domain_ids','Domains','domains'],['topic_ids','Topics','topics'],['hazards','Hazards','hazards'],['risk_functions','Risk and resilience functions','risk_functions']].map(([key,title,facet])=>`<details class="analysis-facet"><summary>${title} <small data-filter-count="${key}">${d.filters[key].length?`${d.filters[key].length} selected`:'All'}</small></summary><div class="analysis-options" role="group" aria-label="${title}">${catalog.facets[facet].map(o=>{const id=typeof o==='string'?o:o.id;return `<label class="check-choice"><input type="checkbox" data-analysis-filter="${key}" value="${esc(id)}" ${d.filters[key].includes(id)?'checked':''}>${esc(typeof o==='string'?human(o):o.name||o.label)}</label>`;}).join('')}</div></details>`).join('');
}

export function renderGroups(d,catalog,region){
 if(d.task!=='compare')return '';
 const mode=catalog.comparison_modes.find(m=>m.id===d.comparison_mode);
 const manual=mode.grouping==='manual';
 return `<div class="control-block"><label>Comparison columns<select id="comparison-mode">${catalog.comparison_modes.map(m=>`<option value="${m.id}" ${d.comparison_mode===m.id?'selected':''}>${esc(m.label)}</option>`).join('')}</select></label><p class="muted">${esc(mode.help)}</p>${manual?`<div class="group-labels">${d.groups.map((g,i)=>`<label>${mode.labels?.[i]||'Group '+(i+1)}<input data-group-label="${i}" value="${esc(g.label)}"></label>`).join('')}</div>${d.comparison_mode==='custom'?'<button id="add-group" type="button">Add comparison group</button>':''}<div class="assignment-list">${d.document_ids.map(id=>{const doc=region.documents.find(x=>x.id===id);const index=d.groups.findIndex(g=>g.document_ids.includes(id));return `<label>${esc(doc?.title||id)}<select data-assign="${id}"><option value="">Assign a group</option>${d.groups.map((g,i)=>`<option value="${i}" ${index===i?'selected':''}>${esc(g.label)}</option>`).join('')}</select></label>`;}).join('')}</div>`:''}</div>`;
}

export function renderAnalysis({d,catalog,region,sourceSelection,title}){
 const task=catalog.tasks.find(t=>t.id===d.task),translation=task.pipeline==='translation';
 return title('CREATE A RESULT','What do you need?','Choose an output and sources. Processing and publication are automatic.')+`<div class="analysis-layout"><form id="analysis-form">
 <section class="paper"><div class="task-grid">${catalog.tasks.map(t=>`<label class="task-choice ${d.task===t.id?'chosen':''}"><input type="radio" name="task" value="${t.id}" ${d.task===t.id?'checked':''}><span><strong>${esc(t.label)}</strong><small>${esc(t.description)}</small></span></label>`).join('')}</div>
 ${task.requires_question?`<label class="full-label">Your question<textarea id="policy-question" rows="3" placeholder="What would you like to find out?">${esc(d.question)}</textarea></label>`:''}</section>
 <section class="paper"><h2>Sources</h2>${sourceSelection()}${renderGroups(d,catalog,region)}</section>
 <details class="paper output-options"><summary>Customize this output</summary>${translation?'<p>Original and aligned English copies are retained.</p>':`<fieldset><legend>Include</legend>${task.options.map(o=>`<label class="check-choice"><input type="checkbox" data-output="${o.id}" ${d.requested_fields.includes(o.id)?'checked':''}>${esc(o.label)}</label>`).join('')}</fieldset>`}
 ${task.allows_filters?`${subjectFilters(d,catalog)}<button type="button" id="clear-analysis-filters">Clear topic filters</button>`:''}
 ${d.task==='gaps'?`<label><input type="checkbox" id="proposals" ${d.include_analyst_proposals?'checked':''}> Include clearly labeled suggestions</label>`:''}
 <label class="full-label">Additional instructions<textarea id="extra-instructions" rows="3">${esc(d.instructions)}</textarea></label>${modelControls(d.model,'analysis-ai')}<button type="button" data-output-settings>Default method & output settings</button></details></form>
 <aside class="request-aside"><section class="paper"><h2>${esc(task.label)}</h2><div id="request-preview" aria-live="polite"></div><p id="request-error" role="status"></p>${selectionProblem(d.model,ai.status)?`<p class="small-note">${esc(selectionProblem(d.model,ai.status))} <button data-nav="ai">Connect AI</button></p>`:''}<button id="save-request" class="primary" type="submit" form="analysis-form">Generate ${translation?'translation':'result'}</button><p class="small-note">OCR, extraction and checks run automatically. The finished result appears in Reports & analysis.</p><details><summary>Save these choices for later</summary><label>Preset name<input id="request-name" maxlength="100" value="${esc(d.name||task.label)}"></label><button id="keep-request" type="button">Save preset</button><button id="download-analysis-request" type="button">Download choices</button></details><div id="request-success" hidden role="status"></div></section></aside></div>`;
}

export function renderRequestPreview(d,catalog,region,compiled,error){
 const t=catalog.tasks.find(t=>t.id===d.task);
 const selected=Object.values(d.filters).flat();
 return `<p><strong>${d.document_ids.length}</strong> document${d.document_ids.length===1?'':'s'} selected</p>${compiled&&d.task==='compare'?`<p class="muted">${compiled.source_groups.map(g=>`${esc(g.label)}: ${g.document_ids.length}`).join('<br>')}</p>`:''}<p>${t.pipeline==='translation'?'Full documents → English + original + bilingual copies':d.task==='compare'?'Comparison matrix: selected dimensions × source groups':d.task==='extract'?'Evidence table with selected fields':d.task==='gaps'?'Source-stated needs and missing-information checks':'Question-led brief with cited evidence annex'}</p>${t.requires_question&&d.question?`<p><strong>Question:</strong> ${esc(d.question)}</p>`:''}${t.allows_filters?`<p class="scope-note">Subject: ${selected.length?selected.map(id=>esc(Object.values(catalog.facets).flat().find(x=>x.id===id)?.name||Object.values(catalog.facets).flat().find(x=>x.id===id)?.label||human(id))).join(' · '):'All selected evidence'}</p>`:''}<details><summary>Selected documents and output details</summary><ul>${d.document_ids.map(id=>`<li>${esc(region.documents.find(doc=>doc.id===id)?.title||id)}</li>`).join('')}</ul><ul>${t.options.filter(o=>d.requested_fields.includes(o.id)).map(o=>`<li>${esc(o.effect)}</li>`).join('')}</ul>${d.task==='gaps'&&d.include_analyst_proposals?'<p>Includes separately labeled support suggestions.</p>':''}${d.instructions?'<p class="small-note">Additional instructions are included in the request.</p>':''}<p class="scope-note">Original and English text remain linked. Saved translations are reused. ${d.uploads.length?'Pending uploads must be registered before execution.':''}</p><p class="small-note muted">${esc(selectionSummary(d.model))}</p></details>`;
}

// Keep a country's choices visible when its last selected document is cleared,
// including requests reopened from storage (which contain only selected IDs).
export function toggleSource(d,id,checked,documents){
 const code=documents.find(doc=>doc.id===id)?.country_code;
 if(code)d.sourceCountries=[...new Set([...(d.sourceCountries||[]),code])];
 d.document_ids=checked?[...new Set([...d.document_ids,id])]:d.document_ids.filter(value=>value!==id);
}

// A later file can fail after earlier registrations succeeded. Refresh the
// registry in either case so those originals stay visible and selectable.
export async function uploadSourceFiles(files,{readFile,register,refresh,onProgress=()=>{},onRegistered=()=>{}}){
 if(files.some(file=>file.size>25000000))throw Error('PDF files must be no larger than 25 MB.');
 let count=0;
 try{for(const file of files){onProgress(file.name);const added=await register(file,await readFile(file));count++;onRegistered(added);}}
 finally{if(count)await refresh();}
 return count;
}
