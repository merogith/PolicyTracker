import {esc,list} from './evidence-reader.js';
import {label,cellText} from '../../integrations/javascript/evidence-model.mjs';
import {deliveryMatrix} from './report-components.js';
export const REPORT_TYPES={country:'Country Profile',extract:'Evidence extraction',compare:'Policy comparison',gaps:'Implementation-information review',brief:'Question-led briefing',translate:'Translation reader'};
export function demoProfile(base,type='country',variant='current'){
 const p=structuredClone(base);p.id=`design-example-${variant==='earlier'?'v1':variant==='empty'?'empty':'v2'}-${type}`;p.report_type=type;
 if(variant==='earlier'){
   p.created_at='2025-10-01T09:00:00Z';p.extraction.records=p.extraction.records.slice(0,5);
   const ids=new Set(p.extraction.records.map(r=>r.local_id)),eids=new Set(p.extraction.records.flatMap(r=>r.evidence_ids));
   p.extraction.evidence=p.extraction.evidence.filter(e=>eids.has(e.local_id));
   const segments=new Set(p.extraction.evidence.map(e=>e.segment_id));
   p.sources=p.sources.map(d=>({...d,segments:d.segments.filter(s=>segments.has(s.id))})).filter(d=>d.segments.length);
   p.extraction.coverage=p.extraction.coverage.filter(c=>segments.has(c.segment_id));
   p.report.headline_findings=p.report.headline_findings.filter(f=>f.citations.record_ids.every(id=>ids.has(id)));
   p.report.sections=p.report.sections.map(s=>({...s,findings:s.findings.filter(f=>f.citations.record_ids.every(id=>ids.has(id)))})).map(s=>s.state==='found'&&!s.findings.length?{...s,state:'not_found_in_scope',gap_note:'No finding saved in this illustrative version.'}:s);
   p.report.prioritized_commitments=[];p.report.followup_questions=[];delete p.reconciliation;
   p.validation_codebook.guide_version='synthetic-historical-example';
   p.validation_codebook.topics.find(t=>t.id==='CLM-04').definition='Archived illustrative definition: warning and preparedness measures. This snapshot remains fixed.';
 }
 if(variant==='empty'){p.extraction={records:[],evidence:[],coverage:[],issues:[]};p.report.headline_findings=[];p.report.prioritized_commitments=[];p.report.followup_questions=[];p.report.sections=p.report.sections.map(s=>({...s,findings:[],state:'not_processed',gap_note:'No extraction is available in this synthetic state.'}));delete p.reconciliation;}
 if(type==='brief')p.report.headline_findings=p.report.headline_findings.slice(0,1);
 if(type==='gaps')p.report.headline_findings=p.report.headline_findings.slice(1,2);
 return p;
}
export function taskSummary(p,records,v){
 if(!p.report_type||p.report_type==='country'||p.report_type==='translate')return '';
 if(!p.extraction.records.length)return '<section class="task-summary"><h2>No extracted evidence is available</h2><p>This illustrative state has no report answer or comparison to read. Source absence and implementation progress cannot be assessed.</p></section>';
 if(p.report_type==='gaps')return `<section class="task-summary"><h2>Stated needs and missing implementation information</h2><p>Review extracted information in scope. Source absence is established only by a recorded missing reason. Support suggestions require a separate analysis request.</p>${deliveryMatrix(p,records,v?.filters)}</section>`;
 if(p.report_type==='compare'){
   const has=id=>p.extraction.records.some(r=>r.local_id===id);
   const limit=has('design-r-7')&&has('design-r-8')?'25% against business as usual and 40% against a historical baseline are incompatible. The 2030 and 2032 warning-system dates have unresolved continuity.':'This earlier illustrative version contains one source edition, so a comparison between editions is unavailable.';
   const kinds=[['Targets and conditions',r=>r.targets.length,'targets'],['Responsibilities',r=>r.actors.length,'actors'],['Finance and support',r=>r.finance.length||r.details.some(d=>d.kind==='support_need'),'finance'],['Risks and resilience',r=>r.risk_contexts.length||r.labels.hazards.length,'risk']];
   return `<section class="task-summary"><h2>What differs between the invented editions?</h2><p class="callout">Comparability limit · full saved scope: ${esc(limit)} No numerical change is calculated.</p><p>Same record filters apply to both columns. A blank cell means no extracted matching value, not proof of source absence. Group membership uses document/evidence links.</p><div class="table-scroll" role="region" aria-label="Policy comparison matrix" tabindex="0"><table class="data-table comparison-table"><thead><tr><th>Dimension</th>${p.sources.map(s=>`<th>${esc(s.title)}</th>`).join('')}</tr></thead><tbody>${kinds.map(([title,accept,column])=>`<tr><th scope="row">${title}</th>${p.sources.map(s=>{const seg=new Set(s.segments.map(x=>x.id));const eids=new Set(p.extraction.evidence.filter(e=>seg.has(e.segment_id)).map(e=>e.local_id));const rows=records.filter(r=>accept(r)&&r.evidence_ids.some(id=>eids.has(id)));return `<td>${rows.map(r=>`<p><button class="table-link" data-record="${esc(r.local_id)}">${esc(r.label_en)}</button><br>${esc(cellText(p,r,column,v?.filters))}</p>`).join('')||'No extracted matching value in this group'}</td>`;}).join('')}</tr>`).join('')}</tbody></table></div></section>`;
 }
 if(p.report_type==='brief')return `<section class="task-summary"><h2>Question: What needs clarification before supporting flood preparedness?</h2><p class="brief-lead">Clarify the financing condition${p.extraction.records.some(r=>r.local_id==='design-r-11')?' and the conflicting deadlines in the invented editions':''}. These statements do not establish current implementation progress.</p><p class="muted">Saved example answer · full example scope; filtering the annex does not rewrite this answer.</p><button class="table-link" data-record="design-r-1">Inspect financing-condition evidence →</button></section>`;
 return `<section class="task-summary"><h2>Extracted evidence at a glance</h2><p>${records.length} source records in the current view. Choose a perspective, group by topic or record type, and inspect each statement’s evidence. Quantitative and qualitative information stay together.</p></section>`;
}
export function demoHeader(type,variant,view){return `<div class="title-row demo-title"><div><div class="eyebrow">SAMPLE REPORT</div><h1>${REPORT_TYPES[type]}</h1><p class="muted">Invented example · not a national policy assessment.</p></div></div><details class="demo-controls"><summary>Choose report type or example state</summary><div class="demo-control-fields"><button id="saved-example">Open saved local example</button><label>Report type<select id="demo-type">${Object.entries(REPORT_TYPES).map(([k,v])=>`<option value="${k}" ${type===k?'selected':''}>${v}</option>`).join('')}</select></label><label>Example state<select id="demo-state">${Object.entries({current:'Partial coverage',earlier:'Earlier illustrative version',outdated:'Newer sources pending',failed:'Failed update; previous report retained',empty:'No extracted records'}).map(([k,v])=>`<option value="${k}" ${variant===k?'selected':''}>${v}</option>`).join('')}</select></label></div></details><nav class="country-nav" aria-label="Sample profile"><button data-demo-view="brief" aria-pressed="${view==='brief'}">Overview</button><button data-demo-view="commitments" aria-pressed="${view==='commitments'}">Policy register</button><button data-demo-view="documents" aria-pressed="${view==='documents'}">Documents & translations</button></nav>${variant==='failed'?'<p class="callout">Synthetic failed update: a source page could not be processed. The previous illustrative report remains available. No real job failed or ran.</p>':''}`;}
