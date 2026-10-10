import {aiRequest} from './ai-view.js';
import {requiresReview} from './generation-view.js';
import {esc,evidenceReader,openReader,translationNotes,extractionNotes,recordDetails,sourceCoverage,publicationControl} from './evidence-reader.js';
import {recordTable} from './report-components.js';
import {csvCell} from '../../integrations/javascript/evidence-model.mjs';
const label=k=>({source_fact:'Source statement',source_reported_observation:'Source-reported observation',derived:'Analysis',analyst_suggestion:'Analyst suggestion',not_found_in_scope:'No finding in the selected sources',not_processed:'Not processed',descriptive_only:'Descriptive comparison only',not_comparable:'Not comparable',label_en:'Statement',description_en:'Details',source_stated_action:'Source-stated action',missing_information:'Missing information',verification_questions:'Questions to verify',proposed_support_activity:'Suggested support',proposed_indicator:'Suggested indicator'})[k]||String(k??'').replaceAll('_',' ').replace(/^./,c=>c.toUpperCase());
const save=(text,name,type)=>{const url=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};

export function operationHistory(runs,catalog){
 const item=r=>`<article class="report-item"><span class="badge neutral">${r.synthetic?'Synthetic · ':''}${r.status==='completed'?(r.published===false?'Unpublished':'Published'):esc(r.status)}</span><h2>${esc(catalog.tasks.find(t=>t.id===r.operation.task)?.label)}</h2><p>${r.operation.question?esc(r.operation.question)+' · ':''}${esc(r.created_at.slice(0,10))} · ${r.document_ids.length} ${r.document_ids.length===1?'document':'documents'}</p>${r.status!=='completed'?`<p>${esc(r.message)}</p>`:''}<details><summary>Request and processing details</summary><p>${esc(r.message)} · ${r.completed}/${r.total}</p><button data-operation-request="${esc(r.id)}">Download frozen request</button></details>${r.error?`<p role="status" class="callout">${esc(r.error)}</p>`:''}${r.status==='completed'?`<button data-operation="${esc(r.id)}">Read saved result</button>${publicationControl(r)}`:''}${requiresReview(r)?'<p class="small-note">This older run used manual preparation. Create a new analysis to use automatic recovery.</p>':''}${['failed','stopped'].includes(r.status)&&r.can_resume!==false&&!requiresReview(r)?`<button data-operation-action="resume" data-id="${esc(r.id)}">Resume run</button>`:''}${r.status==='running'?`<button data-operation-action="stop" data-id="${esc(r.id)}">Stop after current request</button>`:''}</article>`;
 const hidden=runs.filter(r=>r.status==='completed'&&r.published===false),visible=runs.filter(r=>r.status!=='completed'||r.published!==false);
 return (visible.map(item).join('')||'<p>No published analysis results yet. Create an analysis to begin.</p>')+(hidden.length?`<details><summary>Unpublished results · ${hidden.length}</summary>${hidden.map(item).join('')}</details>`:'');
}

// Escape every source/model value; only application-owned markup is inserted.
export function renderOperation(result,{originalLinks=true}={}){
 const findings=[];
 function value(v){
  if(v===null)return '<span class="muted">No extracted value / not requested</span>';
  if(Array.isArray(v))return v.length?`<div>${v.map(item=>`<div class="narrative-section">${value(item)}</div>`).join('')}</div>`:'<span class="muted">None in this result</span>';
  if(typeof v==='object'){
   if('text_en' in v&&v.citations){const i=findings.push(v)-1;return `<article class="finding"><small>${esc(label(v.kind))}</small><p>${esc(v.text_en)}</p><p>${(v.limitations||[]).map(esc).join(' · ')}</p><button data-operation-evidence="${i}">Inspect cited evidence</button></article>`;}
   return `<dl>${Object.entries(v).map(([k,x])=>`<dt><strong>${esc(label(k))}</strong></dt><dd>${value(x)}</dd>`).join('')}</dl>`;
  }
  return esc(v);
 }
 function table(rows,fields){return `<div class="table-scroll" tabindex="0" role="region" aria-label="Analysis result table"><table class="data-table"><thead><tr>${fields.map(f=>`<th>${esc(label(f))}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${fields.map(f=>`<td>${value(r[f]??null)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;}
 const out=result.output;
 let content='';
 if(result.request.task==='compare')content=`<div class="table-scroll" tabindex="0" role="region" aria-label="Analysis result table"><table class="data-table"><thead><tr><th>Dimension</th>${out.groups.map(g=>`<th>${esc(g.label)}</th>`).join('')}<th>Comparability</th></tr></thead><tbody>${out.rows.map(r=>`<tr><th>${esc(label(r.dimension))}</th>${r.cells.map(c=>`<td><p>${esc(label(c.state))}</p>${value(c.findings)}</td>`).join('')}<td><p>${esc(label(r.comparability))}</p><p>${esc(r.comparability_reason)}</p></td></tr>`).join('')}</tbody></table></div><h2>Findings across groups</h2>${value(out.synthesis)}${value(out.exclusions)}`;
 else if(result.request.task==='gaps')content=table(out.rows,['source_stated_action','missing_information','verification_questions',...(result.request.include_analyst_proposals?['proposed_support_activity','proposed_indicator']:[])]);
 else if(!['translate','extract'].includes(result.request.task))content=`${result.request.question?`<h2>${esc(result.request.question)}</h2>`:''}${value(out.headline_findings)}${out.sections.map(s=>`<details class="thematic-section"><summary>${esc(label(s.section_id))}${s.state!=='found'?` · ${esc(label(s.state))}`:''}</summary>${value(s.findings)}${s.gap_note?`<p>${esc(s.gap_note)}</p>`:''}</details>`).join('')}${out.followup_questions.length?`<h2>Follow-up questions</h2>${value(out.followup_questions)}`:''}`;
 if(result.request.task==='extract'){
  const columns=['statement',...result.request.requested_fields.map(f=>({risk_context:'risk',indicators:'monitoring'})[f]||f),'sources'];
  content=`${result.extraction.records.length?recordTable(result,result.extraction.records,{columns,group:'none',filters:{}}):'<p>No records match the selected filters. The scope has not been broadened.</p>'}<details><summary>Analysis of these records</summary>${value(out.headline_findings)}${(out.sections||[]).map(s=>`<h3>${esc(label(s.section_id))}</h3>${value(s.findings)}${s.gap_note?`<p>${esc(s.gap_note)}</p>`:''}`).join('')}</details>`;
 }

 content+=extractionNotes(result);
 const body=`<p class="badge neutral">${result.synthetic?'Synthetic · ':''}Saved separate analysis · ${esc(result.request.task)}</p><h1>${esc(({extract:"Extracted policy information",compare:"Policy comparison",gaps:"Implementation information",brief:"Policy brief",translate:"Documents & translations"})[result.request.task])}</h1><p>Saved ${esc(result.created_at.slice(0,10))} · ${result.sources.length} source ${result.sources.length===1?'document':'documents'}</p><details><summary>Scope and qualifications${result.request.task==='translate'?'':` · ${result.extraction.records.length} source records`}</summary><p>Software checks passed; semantic accuracy is not certified.</p><p>${result.limitations.map(esc).join(' ')}</p></details><details class="operation-export"><summary>Export</summary><div class="inline-actions"><button data-operation-export="json">Download complete JSON</button><button data-operation-export="html">Download readable HTML</button><button data-operation-export="csv">Download result CSV</button></div></details>${publicationControl(result)}${sourceCoverage(result)}${content}${result.request.task==='translate'?'':'<h2>Documents and bilingual evidence</h2>'}${result.sources.map((d,i)=>`<section><h3>${esc(d.title)}</h3><p>${esc(d.country_code)} · ${d.pages} document pages · ${new Set(d.segments.map(s=>s.page)).size} pages with saved text</p><details><summary>Source identity</summary><p>${esc(d.document_id)} · ${esc(d.sha256)}</p></details>${originalLinks&&d.path?.toLowerCase().endsWith('.pdf')?`<a href="/api/ai/documents/${encodeURIComponent(result.id)}/${encodeURIComponent(d.document_id)}" download>Download archived original PDF</a>`:''} <button data-operation-source="${i}">Download English text</button><details ${result.request.task==='translate'?'open':''}><summary>Read aligned original and English</summary><label>Page<select data-operation-page="${i}">${[...new Set(d.segments.map(s=>s.page))].map(page=>`<option value="${page}">Page ${page}</option>`).join('')}</select></label><div data-operation-pages="${i}">${d.segments.map(s=>`<article data-page="${s.page}" ${s.page!==d.segments[0]?.page?'hidden':''}><h4>Page ${s.page} · ${esc(label(s.translation_method))}</h4><div class="bilingual"><section><h3>Original</h3><p class="source-text" lang="${esc(s.language||'und')}" dir="auto">${esc(s.text)}</p></section><section><h3>English</h3><p class="source-text" lang="en">${esc(s.english_text)}</p></section></div>${translationNotes(s)}</article>`).join('')}</div></details></section>`).join('')}<h2>Task limitations</h2>${value(out.limitations||[])}<details><summary>Evidence annex, exact request and execution receipts</summary><pre class="code-sample">${esc(JSON.stringify({request:result.request,extraction:result.extraction,generation:result.generation,validation:result.validation},null,2))}</pre></details>`;
 return {body,findings};
}

export function operationCSV(result){
 const selected=result.request.task==='extract'?result.evidence_table:result.request.task==='translate'?result.sources.flatMap(s=>s.segments.map(segment=>({document_id:s.document_id,source_sha256:s.sha256,...segment}))):result.output.rows||result.output.sections;
 const rows=selected.map(r=>({...r,extraction_notes:result.extraction?.notes||[],source_coverage:result.source_coverage||[],limitations:result.output.limitations||[]}));
 const fields=rows.length?[...new Set(rows.flatMap(Object.keys))]:['local_id','label_en','evidence_ids'];
 const cell=x=>csvCell(typeof x==='object'?JSON.stringify(x):x);
 return [fields,...rows.map(r=>fields.map(f=>r[f]))].map(row=>row.map(cell).join(',')).join('\r\n');
}

export function readableOperationExport(result){
 const {body,findings}=renderOperation(result,{originalLinks:false});
 const content=body.replace(/<button\b[^>]*data-record[^>]*>([\s\S]*?)<\/button>/g,'<strong>$1</strong>').replace(/<button\b[^>]*>[\s\S]*?<\/button>/g,'').replace(/<select\b[^>]*>[\s\S]*?<\/select>/g,'').replace(/ hidden(?=[ >])/g,'');
 return `<!doctype html><html lang="en"><meta charset="utf-8"><title>Saved analysis · ${esc(result.id)}</title><style>body{font:16px/1.6 system-ui;max-width:1000px;margin:40px auto;padding:20px}pre{white-space:pre-wrap;overflow-wrap:anywhere}.bilingual{display:grid;grid-template-columns:1fr 1fr;gap:20px}@media(max-width:650px){.bilingual{display:block}}</style><p>Saved version ${esc(result.id)}. Open original PDFs from this saved version in the local tracker.</p>${content}${result.request.task==='extract'?result.extraction.records.map(r=>`<h2>${esc(r.label_en)}</h2>${recordDetails(result,r,{originalLinks:false})}`).join(''):''}${findings.map(f=>`<h2>Citation annex</h2><p>${esc(f.text_en)}</p>${evidenceReader(result,f.citations.evidence_ids,{originalLinks:false})}`).join('')}</html>`;
}

export async function openOperation(id,detail,onPublication){
 const result=await aiRequest('/analyses/'+encodeURIComponent(id)),{body,findings}=renderOperation(result);
 detail('Saved analysis',body);
 const host=document.getElementById('detail-body');
 host.querySelector('[data-publication]')?.addEventListener('click',async e=>{const b=e.currentTarget;b.disabled=true;try{await aiRequest('/publication',{id,published:b.dataset.published==='true'});await onPublication?.();await openOperation(id,detail,onPublication);}catch(error){b.disabled=false;openReader('Could not update publication',esc(error.message));}});
 host.querySelectorAll('[data-operation-page]').forEach(c=>c.onchange=()=>host.querySelector(`[data-operation-pages="${c.dataset.operationPage}"]`).querySelectorAll('[data-page]').forEach(p=>p.hidden=p.dataset.page!==c.value));
 host.querySelectorAll('[data-record]').forEach(b=>b.onclick=()=>{const r=result.extraction.records.find(r=>r.local_id===b.dataset.record);if(r)openReader(r.label_en,recordDetails(result,r));});
 host.querySelectorAll('[data-operation-evidence]').forEach(b=>b.onclick=()=>{const f=findings[Number(b.dataset.operationEvidence)];openReader('Cited original and English evidence',`<p>${esc(f.text_en)}</p>${evidenceReader(result,f.citations.evidence_ids)}`);});
 host.querySelectorAll('[data-operation-source]').forEach(b=>b.onclick=()=>{const s=result.sources[Number(b.dataset.operationSource)];save(s.segments.map(x=>`Page ${x.page} · ${x.id}\n${x.english_text}${(x.translation_notes||[]).length?"\nTranslation notes: "+x.translation_notes.join("; "):""}`).join('\n\n'),`${s.document_id}-${result.id}-english.txt`,'text/plain;charset=utf-8');});
 host.querySelectorAll('[data-operation-export]').forEach(b=>b.onclick=async()=>{const kind=b.dataset.operationExport;if(kind==='json'){try{const archive=await aiRequest('/analyses/'+encodeURIComponent(id)+'?archive=1');save(JSON.stringify(archive,null,2),id+'.json','application/json');}catch(e){openReader('Export unavailable',esc(e.message));}}else if(kind==='csv')save(operationCSV(result),id+'.csv','text/csv;charset=utf-8');else save(readableOperationExport(result),id+'.html','text/html;charset=utf-8');});
}
