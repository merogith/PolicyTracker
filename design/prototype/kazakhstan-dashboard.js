const scoreMeta=[
  {label:'Context / outcome only',short:'Context / outcome',color:'s0'},
  {label:'Commitment / target',short:'Commitment / target',color:'s1'},
  {label:'Defined action',short:'Defined action',color:'s2'},
  {label:'Resourced / underway',short:'Resourced / underway',color:'s3'},
  {label:'Delivered output',short:'Delivered output',color:'s4'}
];
const signalMeta=[
  {id:'red',label:'Worsening / setback',short:'Worsening',color:'signal-red',weight:-1},
  {id:'orange',label:'Mixed / conflicting evidence',short:'Mixed',color:'signal-orange',weight:0},
  {id:'yellow',label:'Context / outcome only',short:'Context',color:'signal-yellow',weight:0},
  {id:'blue',label:'Commitment / defined action',short:'Planned',color:'signal-blue',weight:1},
  {id:'green',label:'Underway / delivered',short:'Underway',color:'signal-green',weight:1}
];
const esc=value=>String(value??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const idSort=value=>Number(String(value).replace(/\D/g,''))||0;
const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
const allPaths=claim=>claim.subject_paths||[];
const unique=(items,key=value=>value)=>[...new Map(items.map(item=>[key(item),item])).values()];
const facetFields=[
 ['claim_id','Claim ID','Claim'],['statement','Claim text','Claim'],['source_page','Source page','Source'],['segment_id','Source segment ID','Source'],
 ['domain','Domain','Subject'],['subdomain','Subdomain','Subject'],['topic','Topic','Subject'],
 ['statement_type','Statement type','Information'],['purpose','Purpose','Information'],['hazard','Hazard type','Risk'],['risk_component','Risk component','Risk'],
 ['policy_signal','Dashboard signal','Outcome & response'],['outcome_signal','Outcome direction','Outcome & response'],['setback_flag','Explicit setback','Outcome & response'],
 ['affected_group','Affected group','People & themes'],['cross_cutting_theme','Cross-cutting theme','People & themes'],
 ['geographic_scope','Geographic scope','Place & actors'],['place','Place','Place & actors'],['stakeholder','Stakeholder','Place & actors'],['stakeholder_relation','Stakeholder relation','Place & actors'],['policy_status','Policy status','Place & actors'],
 ['fact_type','Quantitative fact type','Numbers & targets'],['metric','Metric / number context','Numbers & targets'],['target_kind','Target kind','Numbers & targets'],['target_value','Target value (source wording)','Numbers & targets'],['unit','Unit','Numbers & targets'],['conditionality','Conditionality','Numbers & targets'],['condition','Condition','Numbers & targets'],['target_period','Target / context period','Numbers & targets'],['baseline','Baseline / reference','Numbers & targets'],['scenario','Scenario / pathway','Numbers & targets'],
 ['finance_type','Finance type','Finance'],['finance_status','Finance status','Finance'],['finance_source','Finance source','Finance'],['finance_amount','Finance amount','Finance'],
 ['document_kind','Document kind','Document'],['document_title','Document title','Document'],['edition_date','Edition date','Document'],['document_language','Document language','Document'],['document_metadata','Combined document metadata','Document'],
 ['relation','Claim relation','Relations'],['evidence_stage','Response evidence stage','Response evidence'],['unmapped_concept','Unmapped concept','Review']
];
const facetFieldMap=Object.fromEntries(facetFields.map(([id,label])=>[id,label]));

function scorePill(score){const meta=scoreMeta[score]||scoreMeta[0];return `<span class="kz-score ${meta.color}" title="Documented response evidence level ${score}"><strong>${score}</strong><span>${meta.short}</span></span>`;}
function signalFor(claim){
 const outcome=claim.outcome_signal||'not_reported';
 if((claim.setback_flags||[]).length||outcome==='worsening')return 0;
 if(outcome==='mixed'||outcome==='not_comparable')return 1;
 if(outcome==='improving')return 4;
 return claim.score===0?2:claim.score<=2?3:4;
}
function signalDistribution(counts){
 const total=counts.reduce((a,b)=>a+b,0)||1;
 return `<div class="kz-distribution" role="img" aria-label="${counts.map((n,i)=>`${n} ${signalMeta[i].label} claims`).join(', ')}">${counts.map((n,i)=>`<span class="${signalMeta[i].color}" style="width:${n/total*100}%" title="${signalMeta[i].label}: ${n} claims"></span>`).join('')}</div><div class="kz-dist-labels">${counts.map((n,i)=>`<span><i class="${signalMeta[i].color}"></i>${signalMeta[i].short} · ${n}</span>`).join('')}</div>`;
}
function topicClaims(topic,data){return data.claims.filter(claim=>(claim.topic_ids||[]).includes(topic.topic_id));}
function topicScore(topic,data){const claims=topicClaims(topic,data);return claims.length===0?-1:claims.some(claim=>claim.score>0)?1:0;}
function topicScoreClass(score){return score<0?'topic-negative':score>0?'topic-positive':'topic-neutral';}
function topicScoreLabel(score){return score<0?'−1 · No claim found':score>0?'+1 · Positive response':'0 · Context only';}
function scoreBand(score){if(score<0)return 'band-red';if(score===0)return 'band-red';if(score<=2)return 'band-orange';if(score<=4)return 'band-yellow';if(score<=6)return 'band-light-green';if(score<=8)return 'band-dark-green';return 'band-blue';}
function topicArrow(score){const band=score<0?'band-dark-red':scoreBand(score);return `<span class="kz-indicator-arrow ${band}" aria-label="${score<0?'down':score>0?'up':'side'} arrow, score ${score}">${score<0?'↓':score>0?'↑':'→'}</span>`;}
function domainState(domain,data){
 const addressed=domain.topics.filter(topic=>topicScore(topic,data)>=0).length;
 const coverage=domain.topic_count===0?'unrated':addressed===0?'none':addressed===domain.topic_count?'all':'partial';
 const direction=domain.score===null?'flat':domain.score>0?'up':domain.score<0?'down':'flat';
 let band='band-unrated';
 if(coverage==='unrated')band='band-unrated';
 else if(coverage==='none')band='band-dark-red';
 else if(coverage==='all')band='band-blue';
 else if(coverage==='partial')band=scoreBand(domain.score);
 const card=coverage==='none'?'domain-no-coverage':coverage==='all'?'domain-all-covered':coverage==='unrated'?'domain-unrated':direction==='up'?'domain-positive':direction==='down'?'domain-negative':'domain-neutral';
 return {addressed,coverage,direction,band,card};
}
function domainRows(data){
 return data.domains.map(domain=>{
  const topics=data.topics.filter(topic=>topic.paths.some(path=>path.domain_id===domain.domain_id));
  const score=topics.reduce((sum,topic)=>sum+topicScore(topic,data),0);
  const claims=new Map(topics.flatMap(topic=>topicClaims(topic,data)).map(claim=>[claim.claim_id,claim]));
  return {...domain,topics,score:topics.length?score:null,topic_count:topics.length,claim_count:claims.size,average:topics.length?score/topics.length:null};
 }).sort((a,b)=>a.domain.localeCompare(b.domain));
}
function radarChart(domains){
 domains=domains.filter(domain=>domain.topic_count>0);
 const cx=250,cy=230,r=158,n=domains.length;
 const point=(index,value,radius=r)=>{const angle=-Math.PI/2+(2*Math.PI*index/n);return [cx+Math.cos(angle)*radius*clamp((value+1)/2,0,1),cy+Math.sin(angle)*radius*clamp((value+1)/2,0,1)];};
 const ring=value=>domains.map((_,i)=>{const [x,y]=point(i,value);return `${i?'L':'M'}${x.toFixed(1)},${y.toFixed(1)}`}).join(' ')+' Z';
 const shortNames={climate:'Climate',disaster_risk:'Disaster risk',food_agriculture:'Food & ag.',water_sanitation:'Water',nature_land:'Nature',energy:'Energy',infrastructure_settlements:'Infra.',transport:'Transport',industry_mining:'Industry',health:'Health',waste_circular:'Waste',economy_transition:'Economy',livelihoods_social_protection:'Livelihoods',tourism:'Tourism'};
 const axes=domains.map((domain,i)=>{const [x,y]=point(i,1);const [lx,ly]=point(i,1,r+29);const angle=-Math.PI/2+2*Math.PI*i/n;const anchor=Math.cos(angle)>.25?'start':Math.cos(angle)<-.25?'end':'middle';return `<line x1="${cx}" y1="${cy}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}"/><text x="${lx.toFixed(1)}" y="${ly.toFixed(1)}" text-anchor="${anchor}"><title>${esc(domain.domain)}</title>${esc(shortNames[domain.domain_id]||domain.domain)}</text>`}).join('');
 const values=domains.map((domain,i)=>{const [x,y]=point(i,domain.average);return `${i?'L':'M'}${x.toFixed(1)},${y.toFixed(1)}`}).join(' ')+' Z';
 return `<div class="kz-radar-wrap"><svg class="kz-radar" viewBox="0 0 500 460" role="img" aria-label="Radar chart of average topic scores by domain, from minus one to plus one"><g class="kz-radar-grid"><path d="${ring(-.5)}"/><path d="${ring(0)}"/><path d="${ring(.5)}"/><path d="${ring(1)}"/>${axes}</g><path class="kz-radar-area" d="${values}"/><g class="kz-radar-points">${domains.map((domain,i)=>{const [x,y]=point(i,domain.average);return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="4"><title>${esc(domain.domain)}: total ${domain.score>0?'+':''}${domain.score} across ${domain.topic_count} topics</title></circle>`}).join('')}</g><text class="kz-radar-zero" x="${cx+5}" y="${cy-4}">0</text></svg><div class="kz-radar-legend"><span><i class="topic-negative"></i>−1 no claims</span><span><i class="topic-neutral"></i>0 context only</span><span><i class="topic-positive"></i>+1 positive response</span></div></div>`;
}
function domainTopics(data,domain){
 return `<div class="kz-indicators">${domain.topics.map(topic=>{const score=topicScore(topic,data);return `<button class="kz-indicator ${topicScoreClass(score)}" data-kz-topic="${esc(topic.topic_id)}" title="${esc(topicScoreLabel(score))}; ${topic.claim_count} claims" aria-label="Open ${esc(topic.label)} claims, score ${score}, ${topic.claim_count} claims"><span class="kz-indicator-id">${esc(topic.topic_id)}</span><strong>${esc(topic.label)}</strong><span class="kz-indicator-count">${topic.claim_count}</span>${topicArrow(score)}</button>`}).join('')||'<span class="kz-no-indicators">No topic indicators defined</span>'}</div>`;
}
function signalPill(claim){const meta=signalMeta[signalFor(claim)];return `<span class="kz-signal-pill ${meta.color}" title="${meta.label}"><i></i>${meta.label}</span>`;}

function dashboard(data){
 const domains=domainRows(data);
 const representedTopics=data.topics.filter(topic=>topic.claim_count>0).length;
 return `<section class="kz-intro paper"><div><span class="kz-demo-badge">DEMO · SELECTED-PAGE PILOT</span><h2>What the NDC documents</h2><p>${esc(data.disclaimer||'A structured view of claims in selected pages. This is evidence coverage, not a country performance rating.')}</p></div><div class="kz-scope"><span>Document</span><strong>${esc(data.title)}</strong><span>Selected pages</span><strong>${esc(data.sample_pages)}</strong></div></section>
 <section class="kz-metrics" aria-label="Sample coverage"><article><span>Grouped claims</span><strong>${data.claim_count}</strong><small>Each claim links to one or more source records</small></article><article><span>Source records</span><strong>${data.source_record_count}</strong><small>Extracted information before grouping</small></article><article><span>Topics with claims</span><strong>${representedTopics} / ${data.topics.length}</strong><small>Unrepresented topics score −1 for this sample</small></article><article><span>Domains</span><strong>${domains.length}</strong><small>Scored from their assigned topics</small></article></section>
 <section class="kz-panel paper"><div class="kz-section-head"><div><h2>Domain scores</h2><p>Radar uses the average topic score (−1 to +1); each domain card shows its total sum. Arrows point up/down/side for positive/negative/zero totals.</p></div><button class="text-link" data-kz-tab="topics">Open topic tracker →</button></div>${radarChart(domains)}<p class="kz-signal-caveat">Topic score: −1 = no claim in this sample; 0 = claims are context/outcome only; +1 = at least one claim has a positive response score. A −1 is a document coverage gap, not proof of poor country performance. The radar omits domains that have no topic indicators defined in the taxonomy.</p></section>
 <section class="kz-panel paper"><div class="kz-section-head"><div><h2>Domains and topic indicators</h2><p>Each domain score is the sum of its topic scores. Every topic row has its own score and arrow; click it to open matching claims.</p></div></div><div class="kz-domain-score-legend"><span><i class="domain-positive"></i>Positive total · green</span><span><i class="domain-neutral"></i>Zero total · yellow</span><span><i class="domain-negative"></i>Negative total · red</span><span><i class="domain-all-covered"></i>All topics represented · blue</span><span><i class="domain-no-coverage"></i>No topics represented · dark red</span></div><p class="kz-topic-fill-legend"><strong>Topic fill:</strong> <span class="topic-negative">−1 · no claim</span> <span class="topic-neutral">0 · context only</span> <span class="topic-positive">+1 · positive response</span></p><div class="kz-arrow-scale"><strong>Arrow color by score (domain totals and topic scores)</strong><span><i class="band-red"></i>negative / 0</span><span><i class="band-orange"></i>1–2</span><span><i class="band-yellow"></i>3–4</span><span><i class="band-light-green"></i>5–6</span><span><i class="band-dark-green"></i>7–8</span><span><i class="band-blue"></i>&gt;8 / all represented</span><span><i class="band-dark-red"></i>no topics represented</span></div><div class="kz-domain-grid">${domains.map(domain=>{const state=domainState(domain,data);const arrow=state.direction==='up'?'↑':state.direction==='down'?'↓':'→';const score=domain.score===null?'—':`${domain.score>0?'+':''}${domain.score}`;const coverage=domain.topic_count?`${state.addressed}/${domain.topic_count} topics represented`:'No topics defined';return `<article class="kz-domain-card ${state.card}"><div class="kz-domain-heading"><h3>${esc(domain.domain)}</h3><div class="kz-domain-totals"><strong>${score}<small>${domain.topic_count?`total · ${domain.topic_count} topics`:'unscored'}</small></strong><span class="kz-domain-score-arrow ${state.band}" title="${state.direction==='up'?'Positive total':state.direction==='down'?'Negative total':state.direction==='flat'?'Zero total':'Not scored'}">${arrow}</span></div></div><p class="kz-domain-coverage">${coverage} · ${domain.claim_count} distinct claims</p>${domainTopics(data,domain)}</article>`}).join('')}</div><p class="kz-signal-caveat">All topics represented means each topic has at least one claim, including context-only claims. No topics represented means every topic is unrepresented. These are document coverage states.</p></section>
 <section class="kz-panel paper"><div class="kz-section-head"><div><h2>Review flags</h2><p>Important source differences remain visible as review items.</p></div><button class="text-link" data-kz-tab="claims">Review all claims →</button></div><div class="kz-review-grid"><article><span class="kz-review-count">2</span><div><strong>Conflicting numeric reports</strong><p>2024 flood impacts; 2023 energy-sector emissions share.</p></div></article><article><span class="kz-review-count">1</span><div><strong>Ambiguous target wording</strong><p>Irrigation-loss target on page 47 needs source clarification.</p></div></article><article><span class="kz-review-count">1</span><div><strong>Conditional target bases</strong><p>Keep the 2035 conditional target’s BAU and 1990 comparisons distinct.</p></div></article></div></section>`;
}

function topicTracker(data,state){
 const topics=data.topics.filter(t=>!state.kzDomain||t.paths.some(p=>p.domain_id===state.kzDomain)).filter(t=>!state.kzSubdomain||t.paths.some(p=>p.subdomain_id===state.kzSubdomain));
 const domains=data.domains;
 const subdomains=unique(data.topics.flatMap(t=>t.paths).filter(p=>!state.kzDomain||p.domain_id===state.kzDomain),p=>p.domain_id+'/'+p.subdomain_id).sort((a,b)=>a.subdomain.localeCompare(b.subdomain));
 return `<div class="kz-filterbar"><label>Domain<select data-kz-filter="kzDomain"><option value="">All domains</option>${domains.map(d=>`<option value="${esc(d.domain_id)}" ${state.kzDomain===d.domain_id?'selected':''}>${esc(d.domain)}</option>`).join('')}</select></label><label>Subdomain<select data-kz-filter="kzSubdomain"><option value="">All subdomains</option>${subdomains.map(d=>`<option value="${esc(d.subdomain_id)}" ${state.kzSubdomain===d.subdomain_id?'selected':''}>${esc(d.subdomain)}</option>`).join('')}</select></label><button data-kz-clear>Clear filters</button></div>
 <p class="kz-overlap-note">Topic score: −1 = no claim found in this document sample; 0 = context/outcome only; +1 = at least one positive response claim. Click any topic to inspect its claims. A −1 is a documentation gap, not proof of poor country performance.</p>
 <div class="kz-topic-list">${topics.map(topic=>{const score=topicScore(topic,data);return `<button class="kz-topic-row ${topicScoreClass(score)}" data-kz-topic="${esc(topic.topic_id)}"><div class="kz-topic-title"><div><div class="kz-topic-row-name"><span class="kz-topic-code">${esc(topic.topic_id)}</span><h3>${esc(topic.label)}</h3></div><p>${unique(topic.paths,p=>p.domain_id+'/'+p.subdomain_id).map(p=>`${esc(p.domain)} <span>›</span> ${esc(p.subdomain)}`).join(' · ')}</p><small>${esc(topic.summary)}</small></div><div class="kz-topic-totals"><strong class="topic-score-badge">${score>0?'+':''}${score}<span>${score<0?'No claims':score===0?'Context':'Positive'}</span></strong><strong>${topic.claim_count}<span>claims</span></strong>${topicArrow(score)}</div></div><span class="kz-topic-open">Open supporting claims →</span></button>`}).join('')||'<div class="empty-state"><p>No topics match these filters.</p></div>'}</div>`;
}

function claimCard(claim){
 const relation=claim.relation_types||[];
 const paths=unique(allPaths(claim),p=>`${p.domain_id}/${p.subdomain_id}/${p.topic_id}`);
 return `<article class="kz-claim-card"><div class="kz-claim-summary"><div class="kz-claim-id">${esc(claim.claim_id)}<span>${claim.member_record_ids.length} source ${claim.member_record_ids.length===1?'record':'records'}</span></div><div class="kz-claim-main"><h3>${esc(claim.statement)}</h3><div class="kz-tag-row">${paths.map(p=>`<span class="kz-tag" title="${esc(p.domain)} › ${esc(p.subdomain)}">${esc(p.domain)} / ${esc(p.topic)}</span>`).join('')}</div></div><div class="kz-claim-evidence"><div>${claim.pages.map(p=>`<span>p. ${esc(p)}</span>`).join('')}</div>${signalPill(claim)}${scorePill(claim.score)}</div></div>
 <details><summary>Inspect labels, grouping and score rationale</summary><div class="kz-claim-detail"><div><h4>Grouped source records</h4>${claim.records.map(r=>`<article class="kz-source-record"><div><strong>${esc(r.record_id)}</strong> · p. ${esc(r.page)} <span>${esc(r.statement_type.replaceAll('_',' '))}</span></div><p>${esc(r.summary)}</p><small>${esc(r.label_notes)}</small></article>`).join('')}</div><div><h4>Score rationale</h4><p>${esc(claim.score_rationale)}</p>${relation.length?`<p class="kz-relation-note">Relation: ${relation.map(esc).join(' · ')}</p>`:''}<p class="kz-proof-note">This score is the response stage documented by the evidence. It does not measure outcome, effectiveness, or overall country progress.</p></div></div></details></article>`;
}

const hazardTerms=[['compound_or_cascading_hazard','compound or cascading hazard'],['storm_or_high_wind','storm or high wind'],['landslide_or_mudslide','landslide or mudslide'],['disease_or_biological_hazard','disease or biological hazard'],['technological_hazard','technological hazard'],['glacial_lake_outburst','glacial lake outburst'],['water_scarcity','water scarcity'],['extreme_heat','extreme heat'],['extreme_cold','extreme cold'],['heavy_precipitation','heavy precipitation'],['coastal_hazard','coastal hazard'],['sea_level_rise','sea level rise'],['earthquake','earthquake'],['tsunami','tsunami'],['avalanche','avalanche'],['wildfire','wildfire'],['drought','drought'],['flood','flood'],['erosion','erosion']];
const groupTerms=['persons with disabilities','people with health conditions','low-income households','displaced communities','displaced people','farming communities','rural communities','urban communities','older people','children','youth','farmers','herders','fishers','workers','women','men'];
const textMatches=(text,terms)=>terms.filter(term=>new RegExp(`(^|[^a-z])${term.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}([^a-z]|$)`,'i').test(text));
function recordText(claim){return (claim.records||[]).map(r=>`${r.summary||''} ${r.label_notes||''}`).join(' · ');}
function yearTerms(text){return [...new Set(text.match(/\b(?:19|20|21)\d{2}(?:\s*[–-]\s*(?:19|20|21)?\d{2})?\b/g)||[])];}
function quantityTerms(text){return [...new Set(text.match(/(?:USD|EUR|KZT|MtCO₂e|MtCO2e|CO₂e|CO2e|MW|m³|ha|tonnes?|%|bn|billion|million)?\s*\d[\d,.]*(?:\s*(?:%|MtCO₂e|MtCO2e|CO₂e|CO2e|MW|m³|ha|tonnes?|bn|billion|million|USD|EUR|KZT))?/gi)||[])].map(x=>x.trim()).filter(Boolean);}
function rawFacetValues(claim,key,data){
 const paths=allPaths(claim), records=claim.records||[], text=recordText(claim), lower=text.toLowerCase();
 const notes=records.map(r=>r.label_notes||'').join(' · ');
 const values={
  claim_id:[claim.claim_id],statement:[claim.statement],source_page:claim.pages||[],segment_id:[],
  domain:paths.map(p=>p.domain),subdomain:paths.map(p=>p.subdomain),topic:paths.map(p=>p.topic),
  statement_type:records.map(r=>r.statement_type),
  purpose:(notes.match(/purpose:\s*([^;]+)/i)?.[1]||'').split(/[,/]/).map(x=>x.trim()).filter(Boolean),
  hazard:hazardTerms.filter(([id,name])=>new RegExp(`\\b(?:${id.replaceAll('_','[_ -]?')}|${name})\\b`,'i').test(text)).map(([id])=>id),
  risk_component:['hazard','exposure','vulnerability','capacity','impact','systemic_or_cascading_risk'].filter(x=>new RegExp(`\\b${x.replaceAll('_','[_ -]?')}\\b`,'i').test(text)),
  affected_group:(notes.match(/affected groups?:\s*([^;]+)/i)?.[1]||'').split(/[,/]/).map(x=>x.trim()).filter(Boolean).concat(textMatches(lower,groupTerms)),
  cross_cutting_theme:['gender_equality','children_and_youth','disability_and_accessibility','poverty_and_inequality','livelihoods_and_jobs','just_transition','capacity_building','finance','technology','data_and_monitoring','participation','transboundary_cooperation','nature_based_solutions'].filter(x=>new RegExp(`\\b${x.replaceAll('_','[_ -]?')}\\b`,'i').test(text)),
  geographic_scope:(notes.match(/geographic scope:\s*([^;]+)/i)?.[1]||'').split(/[,/]/).map(x=>x.trim()).filter(Boolean),
  place:(notes.match(/places?:\s*([^;]+)/i)?.[1]||'').split(/[,/]/).map(x=>x.trim()).filter(Boolean),
  stakeholder:(notes.match(/stakeholders?:\s*([^;]+)/i)?.[1]||'').split(/[,/]/).map(x=>x.trim()).filter(Boolean),
  stakeholder_relation:(notes.match(/stakeholder relationship:\s*([^;]+)/i)?.[1]||'').split(/[,/]/).map(x=>x.trim()).filter(Boolean),
  policy_status:(notes.match(/policy status:\s*([^;]+)/i)?.[1]||'').split(/[,/]/).map(x=>x.trim()).filter(Boolean),
  fact_type:records.flatMap(r=>{const s=r.statement_type||'';return s==='commitment_or_target'||/\btarget\b/i.test(`${r.summary||''} ${r.label_notes||''}`)?['target']:s==='observed_result_or_impact'?['observation']:s==='projection_or_scenario'?['projection']:s==='finance_information'?['finance']:[]}),
  metric:records.filter(r=>/\d/.test(`${r.summary||''} ${r.label_notes||''}`)).map(r=>r.summary||''),
  target_kind:records.flatMap(r=>r.statement_type==='commitment_or_target'||/\btarget\b|\bmilestone\b/i.test(`${r.summary||''} ${r.label_notes||''}`)?['target']:[]),
  value_unit:quantityTerms(text),target_value:records.filter(r=>r.statement_type==='commitment_or_target'||/\btarget\b|\bmilestone\b/i.test(`${r.summary||''} ${r.label_notes||''}`)).flatMap(r=>quantityTerms(`${r.summary||''} ${r.label_notes||''}`)),
  unit:['MtCO₂e','MtCO2e','CO₂e','CO2e','m³','MW','ha','tonnes','%','USD','EUR','KZT'].filter(x=>new RegExp(`\\b${x.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}\\b`,'i').test(text)),
  conditionality:['partly conditional','unconditional','conditional'].filter(x=>new RegExp(`\\b${x.replaceAll(' ','\\s+')}\\b`,'i').test(text)),
  condition:(text.match(/(?:conditional(?:ly)?|subject to|provided that|with timely)[^.;]*/i)||[]),
  target_period:yearTerms(text),
  baseline:(text.match(/(?:below|relative to|compared with|from|against)\s+(?:the\s+)?(?:1990|2021|2025|BAU|business as usual)[^.;]*/gi)||[]),
  scenario:(text.match(/\bSSP\s*\d(?:[-–.]\d)?\b|\bBAU\b|\bbusiness as usual\b/gi)||[]),
  finance_type:['finance_information','need_or_estimate','domestic_public_budget','international_grant','international_loan','green_finance','private_investment','blended_finance'].filter(x=>lower.includes(x)),
  finance_status:['need_or_estimate','requested','pledged','committed','allocated','mobilized','disbursed','spent','not_stated'].filter(x=>new RegExp(`\\b${x.replaceAll('_','[_ -]?')}\\b`,'i').test(text)),
  finance_source:['Baiterek','Development Bank of Kazakhstan','DBK','MDB','Ministry of Ecology and Natural Resources','MENR'].filter(x=>text.toLowerCase().includes(x.toLowerCase())),
  finance_amount:records.flatMap(r=>(`${r.summary||''} ${r.label_notes||''}`).match(/(?:USD|EUR|KZT)\s*[\d,.]+(?:\s*(?:bn|billion|million|m))?/gi)||[]),
  document_kind:['NDC'],document_title:[data.title],edition_date:[data.document_date],document_language:[],document_metadata:[`NDC · ${data.title} · ${data.document_date}`],
  policy_signal:[signalMeta[signalFor(claim)].label],outcome_signal:[claim.outcome_signal||'not_reported'],setback_flag:claim.setback_flags||[],
  relation:claim.relation_types||[],evidence_stage:[String(claim.score)]
 };
 if(key==='value_unit')return unique(values.value_unit,x=>x.toLowerCase());
 if(key==='target_period')return values.target_period;
 if(key==='condition')return values.condition;
 if(key==='finance_amount')return unique(values.finance_amount,x=>x.toLowerCase());
 if(key==='unmapped_concept')return [];
 return unique((values[key]||[]).filter(Boolean).map(String),x=>x.toLowerCase());
}
function facetText(claim,key,data){return rawFacetValues(claim,key,data).join(' · ');}
function claimSearchText(claim,data){return [claim.claim_id,claim.statement,claim.score_label,claim.score_rationale,signalMeta[signalFor(claim)].label,claim.outcome_signal,claim.setback_flags,claim.member_record_ids,claim.pages,claim.relation_types,recordText(claim),...allPaths(claim).flatMap(p=>[p.domain,p.subdomain,p.topic])].flat(Infinity).join(' ').toLocaleLowerCase();}
function fieldOptions(selected){
 const groups=[...new Set(facetFields.map(([, ,group])=>group))];
 return `<option value="">Choose a label field</option>${groups.map(group=>`<optgroup label="${esc(group)}">${facetFields.filter(([, ,g])=>g===group).map(([id,label])=>`<option value="${id}" ${selected===id?'selected':''}>${esc(label)}</option>`).join('')}</optgroup>`).join('')}`;
}
function sortOptions(selected){
 const groups=[...new Set(facetFields.map(([, ,group])=>group))];
 return `<option value="claim_id" ${selected==='claim_id'?'selected':''}>Claim ID</option>${groups.map(group=>`<optgroup label="${esc(group)}">${facetFields.filter(([id,,g])=>g===group&&id!=='claim_id').map(([id,label])=>`<option value="${id}" ${selected===id?'selected':''}>${esc(label)}</option>`).join('')}</optgroup>`).join('')}`;
}

function claimsView(data,state){
 const paths=data.topics.flatMap(t=>t.paths),domains=unique(paths,p=>p.domain_id).sort((a,b)=>a.domain.localeCompare(b.domain));
 const topicOptions=data.topics.filter(t=>!state.kzDomain||t.paths.some(p=>p.domain_id===state.kzDomain));
 let claims=data.claims.filter(c=>!state.kzDomain||allPaths(c).some(p=>p.domain_id===state.kzDomain)).filter(c=>!state.kzTopic||c.topic_ids.includes(state.kzTopic)).filter(c=>state.kzScore===''||c.score===Number(state.kzScore)).filter(c=>!state.kzSearch||claimSearchText(c,data).includes(state.kzSearch.toLocaleLowerCase())).filter(c=>!state.kzFacet||!state.kzFacetValue||facetText(c,state.kzFacet,data).toLocaleLowerCase().includes(state.kzFacetValue.toLocaleLowerCase()));
 const direction=state.kzSortDirection==='desc'?-1:1;
 claims.sort((a,b)=>direction*(facetText(a,state.kzSort||'claim_id',data).localeCompare(facetText(b,state.kzSort||'claim_id',data),undefined,{numeric:true,sensitivity:'base'}))||idSort(a.claim_id)-idSort(b.claim_id));
 return `<div class="kz-filter-panel"><div class="kz-filterbar kz-claim-filters"><label>Search all claim information<input type="search" data-kz-filter="kzSearch" value="${esc(state.kzSearch)}" placeholder="Text, any label, number, stakeholder, page…"></label><label>Domain<select data-kz-filter="kzDomain"><option value="">All domains</option>${domains.map(d=>`<option value="${esc(d.domain_id)}" ${state.kzDomain===d.domain_id?'selected':''}>${esc(d.domain)}</option>`).join('')}</select></label><label>Topic<select data-kz-filter="kzTopic"><option value="">All topics</option>${topicOptions.map(t=>`<option value="${esc(t.topic_id)}" ${state.kzTopic===t.topic_id?'selected':''}>${esc(t.topic_id)} · ${esc(t.label)}</option>`).join('')}</select></label><label>Evidence stage<select data-kz-filter="kzScore"><option value="">All stages</option>${scoreMeta.map((m,i)=>`<option value="${i}" ${state.kzScore===String(i)?'selected':''}>${i} · ${m.label}</option>`).join('')}</select></label><label>Filter label field<select data-kz-filter="kzFacet">${fieldOptions(state.kzFacet)}</select></label><label>Label value<input type="search" data-kz-filter="kzFacetValue" value="${esc(state.kzFacetValue)}" placeholder="Contains…" ${state.kzFacet?'':'disabled'}></label><label>Sort by<select data-kz-filter="kzSort">${sortOptions(state.kzSort||'claim_id')}</select></label><label>Order<select data-kz-filter="kzSortDirection"><option value="asc" ${state.kzSortDirection!=='desc'?'selected':''}>Ascending</option><option value="desc" ${state.kzSortDirection==='desc'?'selected':''}>Descending</option></select></label><button data-kz-clear>Clear filters</button></div><p class="kz-filter-help">Choose any taxonomy field and a text value to filter it, or use the search box across all labels. Sorting follows the selected field; numbers remain in their source wording and are not compared across units.</p></div>
 <div class="kz-results-count" role="status">Showing <strong>${claims.length}</strong> of ${data.claim_count} claims in the selected sample</div><div class="kz-claim-list">${claims.map(claimCard).join('')||'<div class="empty-state"><h3>No matching claims</h3><p>Clear filters or try a broader search. No matches do not mean a policy is absent.</p></div>'}</div>`;
}

export function renderKazakhstanDashboard(data,state){
 const tabs=[['overview','Dashboard'],['topics','Topic tracker'],['claims','Claims & evidence']];
 const current=tabs.some(([id])=>id===state.kzTab)?state.kzTab:'overview';
 const body=current==='topics'?topicTracker(data,state):current==='claims'?claimsView(data,state):dashboard(data);
 return `<div class="kz-dashboard">${`<div class="title-row"><div><div class="eyebrow">COUNTRY EVIDENCE DEMO</div><h1>Kazakhstan</h1><p class="muted">NDC 3.0 · taxonomy pilot · 26 November 2025</p></div><button class="text-link" data-nav="regional">← Regional picture</button></div>`}<nav class="kz-tabs" aria-label="Kazakhstan pilot dashboard">${tabs.map(([id,label])=>`<button data-kz-tab="${id}" aria-current="${current===id?'page':'false'}">${label}</button>`).join('')}</nav>${body}</div>`;
}

export function bindKazakhstanDashboard(root,state,onRender){
 root.querySelectorAll('[data-kz-tab]').forEach(b=>b.addEventListener('click',()=>{state.kzTab=b.dataset.kzTab;onRender();}));
 root.querySelectorAll('[data-kz-filter]').forEach(control=>control.addEventListener(control.type==='search'?'input':'change',()=>{state[control.dataset.kzFilter]=control.value;if(control.dataset.kzFilter==='kzDomain')state.kzSubdomain='';if(control.dataset.kzFilter==='kzFacet')state.kzFacetValue='';onRender();}));
 root.querySelectorAll('[data-kz-clear]').forEach(b=>b.addEventListener('click',()=>{state.kzDomain='';state.kzSubdomain='';state.kzTopic='';state.kzScore='';state.kzSearch='';state.kzFacet='';state.kzFacetValue='';state.kzSort='claim_id';state.kzSortDirection='asc';onRender();}));
 root.querySelectorAll('[data-kz-domain]').forEach(b=>b.addEventListener('click',()=>{state.kzDomain=b.dataset.kzDomain;state.kzSubdomain='';state.kzTopic='';state.kzTab='claims';onRender();}));
 root.querySelectorAll('[data-kz-topic]').forEach(b=>b.addEventListener('click',()=>{state.kzTopic=b.dataset.kzTopic;state.kzDomain='';state.kzSubdomain='';state.kzTab='claims';onRender();}));
}
