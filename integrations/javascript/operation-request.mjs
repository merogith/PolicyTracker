/** Request compiler only; no inference, uploads, publication or credentials. */
export function compileRequest(draft, catalog, region) {
  const task=catalog.tasks.find(t=>t.id===draft.task);
  if(!task) throw new Error('Choose an analysis task.');
  const known=new Map(region.documents.map(d=>[d.id,d]));
  const ids=[...new Set(draft.document_ids||[])];
  if(ids.some(id=>!known.has(id))) throw new Error('An unknown document was selected.');
  if(ids.some(id=>known.get(id).local_status==='unknown')) throw new Error('Local source availability has not been checked. Restart the preview server and check local sources before generating.');
  if(ids.some(id=>known.get(id).local_available===false)) throw new Error('A selected original is unavailable in this workspace. Restore it or deselect it before generating.');
  if(ids.length<(task.minimum_documents||1)) throw new Error(`Select at least ${task.minimum_documents||1} document${task.minimum_documents===1?'':'s'} for ${task.label.toLowerCase()}.`);
  const fields=[...new Set(draft.requested_fields??task.options.filter(o=>o.default).map(o=>o.id))];
  if(task.options.length&&!fields.length) throw new Error('Choose at least one output field.');
  if(fields.some(id=>!task.options.some(o=>o.id===id))) throw new Error('An output field does not apply to this task.');
  const facets={domain_ids:'domains',topic_ids:'topics',hazards:'hazards',risk_functions:'risk_functions'};
  const filters={};
  for(const [key,vocab] of Object.entries(facets)) {
    const allowed=catalog.facets[vocab].map(v=>typeof v==='string'?v:v.id);
    filters[key]=task.allows_filters?[...new Set(draft.filters?.[key]||[])]:[];
    if(filters[key].some(v=>!allowed.includes(v))) throw new Error(`Unknown ${key} filter.`);
  }
  let groups;
  let mode=null;
  if(draft.task==='compare') {
    mode=draft.comparison_mode;
    const comparison=catalog.comparison_modes.find(m=>m.id===mode);
    if(!comparison) throw new Error('Choose a comparison method.');
    if(mode==='documents') {
      groups=ids.map((id,i)=>({id,label:`Document ${i+1} · ${region.countries.find(c=>c.code===known.get(id).country_code)?.name||known.get(id).country_code} — ${known.get(id).title}`,document_ids:[id]}));
    } else if(mode==='countries') {
      groups=[...new Set(ids.map(id=>known.get(id).country_code))].map(code=>({id:code,label:region.countries.find(c=>c.code===code).name,document_ids:ids.filter(id=>known.get(id).country_code===code)}));
      if(groups.length<2) throw new Error('Country comparison requires at least two countries. Choose Documents to compare files from one country.');
    } else if(mode==='ndc_nap') {
      groups=['NDC','NAP'].map(type=>({id:type,label:type,document_ids:ids.filter(id=>known.get(id).declared_type===type)}));
      if(groups.flatMap(g=>g.document_ids).length!==ids.length) throw new Error('NDC–NAP comparison accepts NDC and NAP documents only. Use custom groups for supporting documents.');
    } else {
      groups=(draft.groups||[]).map((g,i)=>({id:`group-${i+1}`,label:g.label.trim(),document_ids:ids.filter(id=>g.document_ids.includes(id))}));
      const assigned=groups.flatMap(g=>g.document_ids);
      if(assigned.length!==ids.length || new Set(assigned).size!==ids.length) throw new Error('Assign every selected document to exactly one comparison group.');
    }
    if(groups.length<2 || groups.some(g=>!g.document_ids.length||!g.label)) throw new Error('A comparison needs at least two named, non-empty groups.');
    if(comparison.max_groups&&groups.length>comparison.max_groups) throw new Error(`This comparison requires exactly ${comparison.max_groups} groups.`);
    if(new Set(groups.map(g=>g.label.toLocaleLowerCase())).size!==groups.length) throw new Error('Give each comparison group a distinct name.');
    if(mode==='revision' && new Set(ids.map(id=>known.get(id).country_code)).size!==1) throw new Error('Revision comparison requires one country. Use custom groups for a mixed-country comparison.');
    if(mode==='revision' && new Set(ids.map(id=>known.get(id).declared_type)).size!==1) throw new Error('Revision comparison requires editions of the same instrument, not an NDC versus a NAP.');
    const editionSets=groups.map(g=>new Set(g.document_ids.map(id=>known.get(id).edition_id).filter(Boolean)));
    if(editionSets.some((a,i)=>editionSets.some((b,j)=>j>i&&[...a].some(id=>b.has(id))))) throw new Error('These files share a policy edition across comparison groups. Keep translations or copies of one edition together.');
    if(mode==='ndc_nap') {
      if(new Set(ids.map(id=>known.get(id).country_code)).size!==1) throw new Error('NDC–NAP alignment requires one country.');
      if(groups.length!==2 || !groups.every((g,i)=>g.document_ids.every(id=>known.get(id).declared_type===(i===0?'NDC':'NAP')))) throw new Error('Assign NDC documents to the NDC group and NAP documents to the NAP group. Declared types still need source verification.');
    }
  } else groups=[{id:'selected',label:'Selected documents',document_ids:ids}];
  if(filters.domain_ids.length&&filters.topic_ids.some(id=>!catalog.facets.topics.find(t=>t.id===id).domain_ids.some(d=>filters.domain_ids.includes(d)))) throw new Error('The selected topic is outside the selected sector. Choose a matching topic or clear the sector.');
  if(task.requires_question && !draft.question?.trim()) throw new Error('Enter the policy question the brief should answer.');
  if(!['codex_chatgpt','openai_api'].includes(draft.model?.route)||!['default','none','minimal','low','medium','high','xhigh','max','ultra'].includes(draft.model?.effort)||!draft.model?.model) throw new Error('Choose model, effort and usage route.');
  return {schema_version:'2.0.0',kind:'ad_hoc',task:task.id,source_groups:groups,filters,requested_fields:fields,
    comparison_mode:mode,include_analyst_proposals:task.id==='gaps'&&!!draft.include_analyst_proposals,
    question:task.requires_question?draft.question?.trim()||'':'',instructions:draft.instructions?.trim()||'',model:{...draft.model,fallback_allowed:'never'},
    output:{artifact:task.artifact,language:'en',include_original_evidence:true,coverage_mode:'all_selected_documents'},
    uploads:(draft.uploads||[]).map(filename=>({filename,state:'local_pending'})),execution_state:'not_run'};
}

export function describeRequest(request,catalog) {
  const task=catalog.tasks.find(t=>t.id===request.task);
  return {task:task.label,source_count:new Set(request.source_groups.flatMap(g=>g.document_ids)).size,
    groups:request.source_groups.map(g=>`${g.label}: ${g.document_ids.length} ${g.document_ids.length===1?'document':'documents'}`),
    effects:task.pipeline==='translation'?['Preserve the original file and all source text.','Save full English text and a side-by-side original/English copy with aligned page/segment references.','Keep headings, tables, numbers, conditions, terminology notes and translation provenance.']:request.requested_fields.map(id=>task.options.find(o=>o.id===id).effect),
    artifact:request.output.artifact,
    execution_note:request.uploads.length?'Uploads must be registered and inspected before a run.':'Source metadata and model access must be verified before a run.'};
}
