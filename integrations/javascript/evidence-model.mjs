/** Pure presentation over frozen source records. Never relabels, merges or dispatches. */
export const PERSPECTIVES = {summary:'Summary',targets:'Targets',risk:'Risks and resilience',delivery:'Delivery and support'};
export const COLUMNS = {statement:'Statement',kind:'Statement type',topics:'Topics',objectives:'Purpose',targets:'Targets and conditions',risk:'Risk and resilience',actors:'Responsibilities',finance:'Finance and support',monitoring:'Monitoring',sources:'Sources'};
export const DEFAULT_COLUMNS = {
  summary:['statement','kind','topics','sources'], targets:['statement','targets','actors','sources'],
  risk:['statement','risk','topics','sources'], delivery:['statement','actors','finance','monitoring','sources']
};
export const FACETS = {domain:'Domain',topic:'Topic',objectives:'Policy purpose',kind:'Statement type',assertion_kind:'Statement framing',documentation_status:'Document statement',hazards:'Hazard',risk_functions:'Risk and resilience function',risk_components:'Risk component',drr_phases:'DRR phase',resilience_functions:'Resilience function',population_groups:'Population group',cross_cutting_tags:'Cross-cutting theme',policy_instruments:'Policy instrument',source:'Document',actor:'Institution',conditionality:'Target condition',period:'Stated target period',missing:'Missing-value reason',geography:'Geographic scope'};
const DIMENSIONS = {kind:'record_kinds',assertion_kind:'assertion_kinds',documentation_status:'documentation_statuses',conditionality:'conditionalities',missing:'missing_reasons',geography:'geography_scopes'};
export const words = value => String(value ?? '').replaceAll('_',' ');
export const unique = values => [...new Set(values)];
export function label(p, dimension, id) {
  return p.validation_codebook?.dimensions?.find(d=>d.id===dimension)?.options.find(o=>o.id===id)?.label || words(id);
}
export function riskDimension(p) { return p.validation_codebook?.dimensions?.some(d=>d.id==='risk_functions')?'risk_functions':'drr_phases'; }
export function visibleFacets(p) {
 const lean=riskDimension(p)==='risk_functions';
 return Object.fromEntries(Object.entries(FACETS).filter(([key])=>key!=='missing'&&(lean?!['assertion_kind','documentation_status','drr_phases','resilience_functions'].includes(key):key!=='risk_functions')));
}
export function statementText(p,r) {
 return [label(p,'record_kinds',r.kind), ...('assertion_kind' in r?[label(p,'assertion_kinds',r.assertion_kind),label(p,'documentation_statuses',r.documentation_status)]:[])].join(' · ');
}
export function topic(p,id) { return p.validation_codebook?.topics?.find(t=>t.id===id); }
export function domains(p,r) { return unique(r.labels.topic_ids.flatMap(id=>topic(p,id)?.domain_ids || [])); }
export function sourceRefs(p,r) {
  const ev = new Set(r.evidence_ids);
  const segments = new Set(p.extraction.evidence.filter(e=>ev.has(e.local_id)).map(e=>e.segment_id));
  return p.sources.flatMap(d=>{
    const pages=unique(d.segments.filter(s=>segments.has(s.id)).map(s=>s.page)).sort((a,b)=>a-b);
    return pages.length ? [{id:d.document_id,title:d.title,pages}] : [];
  });
}
export function values(p,r,key) {
  if(key==='domain') return domains(p,r);
  if(key==='topic') return r.labels.topic_ids.length ? r.labels.topic_ids : ['__unmapped'];
  if(key==='source') return sourceRefs(p,r).map(d=>d.id);
  if(key==='actor') return r.actors.map(a=>a.name_en);
  if(key==='conditionality') return r.targets.map(t=>t.conditionality);
  if(key==='period') return r.targets.map(t=>t.target_period).filter(Boolean);
  if(key==='missing') return r.missing_fields.map(m=>m.reason);
  if(key==='geography') return [r.geography.scope];
  return Array.isArray(r.labels[key]) ? r.labels[key] : r[key] ? [r[key]] : [];
}
export function valueLabel(p,key,id) {
  if(id==='__unmapped') return 'No mapped topic';
  if(key==='topic') return topic(p,id)?.name || id;
  if(key==='domain') return p.validation_codebook?.domains?.find(d=>d.id===id)?.name || id;
  if(key==='source') return p.sources.find(d=>d.document_id===id)?.title || id;
  if(['actor','period'].includes(key)) return id;
  return label(p,DIMENSIONS[key]||key,id);
}
export function facetOptions(p,key) {
  return unique(p.extraction.records.flatMap(r=>values(p,r,key))).map(id=>({id,label:valueLabel(p,key,id)})).sort((a,b)=>a.label.localeCompare(b.label));
}
export function inPerspective(r,perspective) {
  if(perspective==='targets') return r.kind==='commitment'||r.targets.length>0;
  if(perspective==='risk') return ['hazards','risk_components','risk_functions','drr_phases','resilience_functions'].some(k=>r.labels[k]?.length)||r.labels.objectives.includes('disaster_risk_reduction')||r.risk_contexts.length>0||r.details.some(d=>['risk_context','vulnerability'].includes(d.kind));
  if(perspective==='delivery') return r.kind==='commitment'||r.actors.length>0||r.finance.length>0||r.indicators.length>0||r.details.length>0;
  return true;
}
const selected = value => Array.isArray(value) ? value : value ? [value] : [];
export function matchingTargets(r,filters={}) {
  return r.targets.filter(t=>(!selected(filters.conditionality).length||selected(filters.conditionality).includes(t.conditionality))&&(!selected(filters.period).length||selected(filters.period).includes(t.target_period)));
}
export function filterRecords(p,filters={},perspective='summary') {
  filters={...filters};
  if(filters.hazard) filters.hazards=filters.hazard;
  if(filters.phase) filters.drr_phases=filters.phase;
  const query=(filters.query||'').trim().toLocaleLowerCase();
  return p.extraction.records.filter(r=>{
    if(!inPerspective(r,perspective))return false;
    if((selected(filters.conditionality).length||selected(filters.period).length)&&!matchingTargets(r,filters).length)return false;
    if(!Object.keys(FACETS).filter(k=>!['period','conditionality'].includes(k)).every(k=>!selected(filters[k]).length||values(p,r,k).some(v=>selected(filters[k]).includes(v))))return false;
    if(!query)return true;
    const evidenceIds=new Set(r.evidence_ids), evidence=p.extraction.evidence.filter(e=>evidenceIds.has(e.local_id));
    const segmentIds=new Set(evidence.map(e=>e.segment_id));
    const text=[JSON.stringify(r),...r.labels.topic_ids.map(id=>topic(p,id)?.name||id),...sourceRefs(p,r).map(s=>s.title),...evidence.map(e=>e.quote_original),...p.sources.flatMap(d=>d.segments.filter(s=>segmentIds.has(s.id)).map(s=>s.english_text))].join(' ');
    return text.toLocaleLowerCase().includes(query);
  });
}
export function targetText(t) {
  const number=t.comparator==='range'?`${t.lower?.raw_token??'?'}–${t.upper?.raw_token??'?'}`:`${({at_least:'≥ ',at_most:'≤ ',approximate:'≈ '}[t.comparator]||'')}${t.value?.raw_token??''}`;
  return [t.metric_text,number&&`${number} ${t.unit_raw||''}`.trim(),t.target_period||'No extracted deadline',t.condition_text].filter(Boolean).join(' · ');
}
export function missingText(p,r,path) {
  const missing=r.missing_fields.find(m=>m.field_path===path);
  return missing ? `${label(p,'missing_reasons',missing.reason)}${missing.detail?`: ${missing.detail}`:''}` : 'No extracted value; source absence not established';
}
export function matchingDetails(r,items,filters={}) {
  if(!selected(filters.conditionality).length&&!selected(filters.period).length)return items;
  const targets=new Set(matchingTargets(r,filters).map(t=>t.local_id));
  return items.filter(item=>!item.target_ids?.length||item.target_ids.some(id=>targets.has(id)));
}
export function cellText(p,r,key,filters={}) {
  if(key==='statement')return `${r.label_en}\n${r.description_en}`;
  if(key==='kind')return statementText(p,r);
  if(key==='topics')return r.labels.topic_ids.map(id=>topic(p,id)?.name||id).join('; ')||'No mapped topic';
  if(key==='objectives')return r.labels.objectives.map(id=>label(p,'objectives',id)).join('; ')||'No purpose label recorded';
  if(key==='targets')return matchingTargets(r,filters).map(targetText).join('\n')||'No matching structured target';
  if(key==='risk')return [...['hazards','risk_components','risk_functions','drr_phases','resilience_functions'].flatMap(k=>(r.labels[k]||[]).map(id=>label(p,k,id))),...matchingDetails(r,r.risk_contexts,filters).flatMap(c=>[c.hazard_text,...c.vulnerability_drivers,...c.stated_capacities])].filter(Boolean).join('; ')||'See source context';
  if(key==='actors')return matchingDetails(r,r.actors,filters).map(a=>`${a.name_en} (${label(p,'actor_roles',a.role)})`).join('; ')||missingText(p,r,'/actors');
  if(key==='finance')return [...matchingDetails(r,r.finance,filters).map(f=>`${label(p,'finance_kinds',f.kind)}: ${[f.amount?.raw_token,f.currency,f.description_en].filter(Boolean).join(' ')}`),...matchingDetails(r,r.details,filters).filter(d=>['support_need','barrier','dependency','coordination','implementation_step'].includes(d.kind)).map(d=>`${label(p,'detail_kinds',d.kind)}: ${d.text_en}`),...matchingTargets(r,filters).filter(t=>t.condition_text).map(t=>t.condition_text)].join('\n')||missingText(p,r,'/finance');
  if(key==='monitoring')return matchingDetails(r,r.indicators,filters).map(i=>[i.name_en,i.cadence,i.data_source].filter(Boolean).join(' · ')).join('; ')||missingText(p,r,'/indicators');
  if(key==='sources')return sourceRefs(p,r).map(s=>`${s.title} · ${s.pages.length===1?'page':'pages'} ${s.pages.join(', ')}`).join('; ');
  return '';
}
export function buckets(p,records,key) {
  const map=new Map();
  for(const r of records)for(const id of unique(values(p,r,key))) {
    if(!map.has(id))map.set(id,{id,label:valueLabel(p,key,id),recordIds:[]});
    map.get(id).recordIds.push(r.local_id);
  }
  return [...map.values()].sort((a,b)=>b.recordIds.length-a.recordIds.length||a.label.localeCompare(b.label));
}
export function sortedRecords(p,records,sort='source') {
  if(sort==='source')return records;
  const key=r=>sort==='label'?r.label_en:sort==='kind'?label(p,'record_kinds',r.kind):r.targets.map(t=>t.target_period).filter(Boolean).sort()[0]||'\uffff';
  return [...records].sort((a,b)=>key(a).localeCompare(key(b),undefined,{numeric:true})||a.local_id.localeCompare(b.local_id));
}
export function defaultView(p,perspective='summary') {
  return {schemaVersion:1,profileId:p.id,codebook:{taxonomy:p.validation_codebook?.taxonomy_version||null,vocabulary:p.validation_codebook?.vocabulary_version||null,guide:p.validation_codebook?.guide_version||null},perspective,filters:{query:''},sort:'source',group:'none',columns:[...DEFAULT_COLUMNS[perspective]],sections:{visuals:true,priorities:true,questions:true},name:''};
}
export function validateView(p,view) {
  const errors=[];
  const object=value=>!!value&&typeof value==='object'&&!Array.isArray(value);
  if(!object(view)||view.schemaVersion!==1||!Object.hasOwn(PERSPECTIVES,view.perspective))return ['This view uses an unsupported format or perspective.'];
  if(Object.keys(view).some(k=>!['schemaVersion','profileId','codebook','perspective','filters','sort','group','columns','sections','name'].includes(k))||typeof view.profileId!=='string'||!view.profileId||typeof view.name!=='string'||view.name.length>80)errors.push('The saved view metadata is invalid.');
  if(!object(view.codebook)||Object.keys(view.codebook).some(k=>!['taxonomy','vocabulary','guide'].includes(k))||['taxonomy','vocabulary','guide'].some(k=>view.codebook[k]!==null&&typeof view.codebook[k]!=='string'))errors.push('The saved definition versions are invalid.');
  if(!Array.isArray(view.columns)||!view.columns.includes('statement')||new Set(view.columns).size!==view.columns.length||view.columns.some(c=>!Object.hasOwn(COLUMNS,c)))errors.push('The saved columns are not supported.');
  if(!object(view.sections)||Object.keys(view.sections).some(k=>!['visuals','priorities','questions'].includes(k))||['visuals','priorities','questions'].some(k=>typeof view.sections[k]!=='boolean'))errors.push('The saved section settings are not supported.');
  if(!['source','label','kind','period'].includes(view.sort)||!['none','domain','kind','source'].includes(view.group))errors.push('The saved ordering is not supported.');
  if(!object(view.filters))return [...errors,'The saved filters are invalid.'];
  for(const [key,value] of Object.entries(view.filters||{})) {
    if(key==='query'){if(typeof value!=='string')errors.push('The search text is invalid.');continue;}
    if(!Object.hasOwn(FACETS,key)){errors.push(`Unsupported filter: ${key}`);continue;}
    if(!Array.isArray(value)||value.some(id=>typeof id!=='string')||new Set(value).size!==value.length){errors.push(`${FACETS[key]} must contain distinct selected values.`);continue;}
    if(value.length&&['kind','assertion_kind','documentation_status','risk_functions','drr_phases','resilience_functions'].includes(key)&&view.codebook?.vocabulary!==p.validation_codebook?.vocabulary_version)errors.push('Statement or risk filters use another method version. Choose these filters again; no automatic relabeling is applied.');
    const available=new Set(facetOptions(p,key).map(o=>o.id));
    if(selected(value).some(id=>!available.has(id)))errors.push(`${FACETS[key]} contains values unavailable in this version.`);
  }
  return errors;
}
export function projectDashboard(p,view=defaultView(p)) {
  const records=filterRecords(p,view.filters,view.perspective);
  return {release_id:p.id,count_unit:'source_records',rows:records.map(r=>({commitment_id:r.local_id,record_id:r.local_id,label_en:r.label_en,topic_ids:r.labels.topic_ids,domain_ids:domains(p,r),target_display:cellText(p,r,'targets',view.filters),hazards:r.labels.hazards,[riskDimension(p)]:r.labels[riskDimension(p)]||[],kind:r.kind,evidence_ids:r.evidence_ids}))};
}
export function exportView(p,view) {
  const records=sortedRecords(p,filterRecords(p,view.filters,view.perspective),view.sort);
  const ids=new Set(records.flatMap(r=>r.evidence_ids));
  const include=id=>{const e=p.extraction.evidence.find(e=>e.local_id===id);for(const next of e?.context_evidence_ids||[])if(!ids.has(next)){ids.add(next);include(next);}};
  [...ids].forEach(include);
  const evidence=p.extraction.evidence.filter(e=>ids.has(e.local_id));
  const segments=new Set(evidence.map(e=>e.segment_id));
  return {source_coverage:structuredClone(p.source_coverage||[]),export_kind:'current_filtered_view',profile_id:p.id,country_code:p.country_code,synthetic:!!p.synthetic,presentation_fixture:!!p.presentation_fixture,exported_at:new Date().toISOString(),view:structuredClone(view),counting_unit:'source records, not unique commitments',variant_scope:'Complete parent records and sibling target variants are retained as evidence context. Displayed cells use matching target variants.',record_count:records.length,source_record_total:p.extraction.records.length,narrative_scope:'Saved narrative is not regenerated for these filters and is not included in this record export.',extraction_notes:structuredClone(p.extraction.notes||[]),limitations:[...p.report.limitations,'Multi-label categories overlap. Commitments do not establish progress. Missing values are not zero.'],definitions:p.validation_codebook||null,records:structuredClone(records),evidence:structuredClone(evidence),sources:p.sources.filter(d=>d.segments.some(s=>segments.has(s.id))).map(d=>({...structuredClone(d),segments:structuredClone(d.segments.filter(s=>segments.has(s.id)))}))};
}
export function csvCell(value) {let s=String(value??'');if(/^[\s]*[=+@\-']/.test(s)||/^[\t\r\n]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';}
export function currentViewCSV(p,view) {
  const bundle=exportView(p,view);
  const headings=['profile_id','scope','filters','counting_unit','codebook_versions','limitations','extraction_notes','record_id',...view.columns,'evidence_ids','topic_definitions','missing_reasons','evidence_annex'];
  const lines=bundle.records.map(r=>[p.id,'Current filtered view; full parent records retained in evidence JSON',JSON.stringify(view.filters),bundle.counting_unit,JSON.stringify(view.codebook),bundle.limitations.join(' | '),JSON.stringify(bundle.extraction_notes),r.local_id,...view.columns.map(c=>cellText(p,r,c,view.filters)),r.evidence_ids.join('; '),JSON.stringify(r.labels.topic_ids.map(id=>topic(p,id))),JSON.stringify(r.missing_fields),JSON.stringify(bundle.evidence.filter(e=>r.evidence_ids.includes(e.local_id)).map(e=>({quote_original:e.quote_original,evidence_id:e.local_id,...bundle.sources.flatMap(d=>d.segments.filter(s=>s.id===e.segment_id).map(s=>({document:d.title,page:s.page,english_text:s.english_text,translation_method:s.translation_method})))[0]})))]);
  return '\ufeff'+[headings,...lines].map(row=>row.map(csvCell).join(',')).join('\r\n');
}
