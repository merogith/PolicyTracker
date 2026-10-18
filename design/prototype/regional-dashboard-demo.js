(() => {
  const root = document.querySelector('#app');
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  let data, mode = 'region', selectedCountry = null, selectedDomain = null, query = '', sort = 'sample';
  const country = code => data.countries.find(item => item.code === code);
  const sampleFor = item => data.country_samples[item.code] || null;
  const countryDomains = item => {
    const sample = sampleFor(item);
    if (!sample) return [];
    return data.domains.map(domain => {
      const topics = domain.topics.map(topic => {
        const claims = sample.claims.filter(claim => (claim.topic_ids || []).includes(topic.topic_id));
        return {...topic, claim_count:claims.length, score:claims.length===0?-1:(claims.some(claim => (claim.score || 0)>0)?1:0)};
      });
      const claims = new Set(topics.flatMap(topic => sample.claims.filter(claim => (claim.topic_ids || []).includes(topic.topic_id)).map(claim => claim.claim_id)));
      return {...domain, topics, score:topics.reduce((sum,topic)=>sum+topic.score,0), claim_count:claims.size};
    });
  };
  const state = domain => {
    if (domain.unscored) return {kind:'unscored', arrow:'·', label:'No registered document sample'};
    const topics = domain.topics;
    const addressed = topics.filter(topic => topic.score >= 0).length;
    if (addressed === 0) return {kind:'no-coverage', arrow:'↓', label:'No topic has a claim in this sample'};
    if (addressed === topics.length) return {kind:'covered', arrow:domain.score > 0 ? '↑' : domain.score < 0 ? '↓' : '→', label:'All topics have at least one claim'};
    if (domain.score > 0) return {kind:'positive', arrow:'↑', label:'Positive domain total'};
    if (domain.score < 0) return {kind:'negative', arrow:'↓', label:'Negative domain total'};
    return {kind:'neutral', arrow:'→', label:'Neutral domain total'};
  };
  const scoreText = score => `${score > 0 ? '+' : ''}${score}`;
  const badge = domain => {
    const s = state(domain);
    return `<span class="cell ${s.kind}" title="${esc(s.label)} · total ${scoreText(domain.score)} across ${domain.topic_count} topics"><span>${scoreText(domain.score)}</span><span class="arrow" aria-hidden="true">${s.arrow}</span></span>`;
  };
  function regionView() {
    mode = 'region'; selectedDomain = null;
    const sampled = data.countries.filter(c => c.scored).length;
    let countries = data.countries.filter(c => `${c.name} ${c.code}`.toLowerCase().includes(query.toLowerCase()));
    countries.sort((a,b) => sort === 'documents' ? b.documents-a.documents || a.name.localeCompare(b.name) : sort === 'sample' ? Number(b.scored)-Number(a.scored) || a.name.localeCompare(b.name) : a.name.localeCompare(b.name));
    root.innerHTML = `<header class="topline"><div class="brand"><span>POLICY</span> TRACKER</div><div class="demo-tag">REGIONAL PROTOTYPE · ${esc(data.region.toUpperCase())}</div></header>
      <section class="hero"><div><p class="eyebrow">Climate and disaster policy</p><h1>Regional overview</h1><p>Scan document coverage across ${data.countries.length} countries and compare domain evidence where a reviewed sample exists.</p></div><select class="country-select" id="country-select" aria-label="Open a country profile"><option value="">Open country profile…</option>${data.countries.map(c=>`<option value="${esc(c.code)}">${esc(c.name)}</option>`).join('')}</select></section>
      <section class="metrics"><article class="metric"><strong>${data.countries.length}</strong><span>countries in this regional demo</span></article><article class="metric"><strong>${data.countries.reduce((n,c)=>n+c.documents,0)}</strong><span>registered document records</span></article><article class="metric"><strong>${sampled} / ${data.countries.length}</strong><span>countries with a cited sample in this demo</span></article></section>
      <div class="notice">${esc(data.scope_note)} ${esc(data.method_note)}</div>
      <section><div class="section-head"><div><h2>Country × domain matrix</h2><p>Each cell is the sum of topic evidence scores for that domain. Select a country to see its domain profile.</p></div><div class="tools"><input class="search" id="country-search" placeholder="Find a country" value="${esc(query)}" aria-label="Find a country"><select class="button" id="sort-select" aria-label="Sort countries"><option value="sample" ${sort==='sample'?'selected':''}>Sort: reviewed sample first</option><option value="name" ${sort==='name'?'selected':''}>Sort: country name</option><option value="documents" ${sort==='documents'?'selected':''}>Sort: document count</option></select></div></div>
      <div class="table-wrap"><table class="matrix"><thead><tr><th>Country</th><th class="inventory">Docs</th>${data.domains.map(d=>`<th title="${esc(d.label)}">${esc(d.label)}</th>`).join('')}</tr></thead><tbody>${countries.map(c=>{const byDomain=new Map(countryDomains(c).map(d=>[d.domain_id,d]));return `<tr><td><button class="country-button" data-country="${esc(c.code)}">${esc(c.name)} <span class="country-code">${esc(c.code)}</span></button></td><td class="inventory" title="Catalog metadata, not extracted evidence">${c.documents}</td>${data.domains.map(d=>`<td>${byDomain.has(d.domain_id)?badge(byDomain.get(d.domain_id)):'<span class="cell unscored" title="No registered document sample">—</span>'}</td>`).join('')}</tr>`;}).join('')||`<tr><td colspan="${data.domains.length+2}" class="empty">No countries match this search.</td></tr>`}</tbody></table></div>
      <div class="legend"><span><i class="positive"></i>Positive total</span><span><i class="neutral"></i>Zero total</span><span><i class="negative"></i>Negative total</span><span><i class="covered"></i>All topics represented</span><span><i class="no-coverage"></i>No topics represented</span><span><i class="unscored"></i>Not sampled</span></div>
      <p class="footnote">Domain total = sum of topic scores: no claim found −1; context/outcome only 0; at least one positive response claim +1. Domain arrow follows the total (up, level, down). The colors describe evidence coverage and response signals in the reviewed documents; they do not establish real-world performance or rank countries.</p></section>`;
    root.querySelector('#country-select').addEventListener('change', e => e.target.value && countryView(e.target.value));
    root.querySelector('#country-search').addEventListener('input', e => { query=e.target.value; const start=e.target.selectionStart; regionView(); const input=root.querySelector('#country-search'); input.focus(); input.setSelectionRange(start,start); });
    root.querySelector('#sort-select').addEventListener('change', e=>{sort=e.target.value;regionView();});
    root.querySelectorAll('[data-country]').forEach(btn=>btn.addEventListener('click',()=>countryView(btn.dataset.country)));
  }
  function countryView(code) {
    mode='country'; selectedCountry=code; selectedDomain=null;
    const c=country(code), sample=sampleFor(c), isScored=!!sample, domains=isScored?countryDomains(c):data.domains.map(d=>({...d,score:0,unscored:true}));
    root.innerHTML=`<header class="topline"><div class="brand"><span>POLICY</span> TRACKER</div><div class="demo-tag">COUNTRY PROFILE · DEMO</div></header><button class="back-link" id="back">← Regional overview</button>
      <section class="hero"><div><p class="eyebrow">${esc(c.code)} · Country profile</p><h1>${esc(c.name)}</h1><p>${c.documents} registered documents · ${c.catalog_pages.toLocaleString()} catalog pages · ${isScored?'reviewed selected-page sample available':'no reviewed evidence sample in this demo'}</p></div><select class="country-select" id="country-select" aria-label="Switch country"><option value="">Switch country…</option>${data.countries.map(x=>`<option value="${esc(x.code)}" ${x.code===code?'selected':''}>${esc(x.name)}</option>`).join('')}</select></section>
      ${isScored?`<div class="notice">${esc(sample.source_document_title)}${sample.source_date?` · ${esc(sample.source_date)}`:''}; selected PDF pages ${esc((sample.sampled_pdf_pages||[]).join(', '))}. ${esc(sample.scope_note||'Curated selected-page sample; not a full document review.')} ${code==='KAZ'?esc(data.method_note):'Scores are based only on these cited sample statements; this is not a country performance rating.'}</div>`:`<div class="notice">This country has no registered document in the current corpus, so domain cells remain unscored.</div>`}
      <section><div class="section-head"><div><h2>Domain evidence scores</h2><p>Domain totals sum topic evidence signals; topic counts are shown to make different domain sizes visible.</p></div></div>
      <div class="domain-layout"><div class="domain-list">${domains.map(d=>{const s=state(d);const max=Math.max(3,d.topic_count), pct=Math.min(100,Math.abs(d.score)/max*50);const left=d.score<0?50-pct:50;const bar=`<div class="bar"><i class="zero"></i><i class="fill ${s.kind}" style="left:${left}%;width:${pct}%"></i></div>`;return `<button class="domain-row" data-domain="${esc(d.domain_id)}"><span class="name">${esc(d.label)}</span>${bar}<span class="score">${isScored?scoreText(d.score):'—'} <small>/${d.topic_count}</small></span><span class="arrow ${s.kind}">${isScored?s.arrow:'·'}</span></button>`;}).join('')}</div><aside class="profile-side"><h3>Reading the score</h3><p>Each topic is −1 when no claim is present in this sample, 0 for context or outcome only, and +1 when a positive response claim exists.</p><p>Domain total is the sum of its topic scores. A negative total signals evidence gaps in this document sample, not proof of poor performance.</p><p>There are ${c.documents} registered document records in the catalog; this sample uses ${sample?.claims.length||0} claims from one document.</p></aside></div></section>
      <section id="domain-detail"></section>`;
    root.querySelector('#back').addEventListener('click',regionView);
    root.querySelector('#country-select').addEventListener('change',e=>e.target.value&&countryView(e.target.value));
    if(isScored) root.querySelectorAll('[data-domain]').forEach(btn=>btn.addEventListener('click',()=>domainClaims(btn.dataset.domain)));
  }
  function domainClaims(id) {
    selectedDomain=id;
    const domain=countryDomains(country(selectedCountry)).find(d=>d.domain_id===id);
    const tids=new Set(domain.topics.map(t=>t.topic_id));
    const sample=sampleFor(country(selectedCountry));
    const claims=sample.claims.filter(c=>(c.topic_ids||[]).some(t=>tids.has(t)));
    const detail=root.querySelector('#domain-detail');
    detail.innerHTML=`<div class="section-head"><div><h2>${esc(domain.label)} · supporting claims</h2><p>${claims.length} sample claim${claims.length===1?'':'s'} linked to this domain. Claim scores and source pages are retained.</p></div></div><div class="claim-list">${claims.map(c=>`<article class="claim-card"><p>${esc(c.statement)}</p><div class="meta"><span>${esc(c.claim_id)} · response evidence ${esc(c.score)} · topics ${(c.topic_ids||[]).map(esc).join(', ')}</span><span>${esc(c.source_document_title||sample.source_document_title)} · p. ${esc((c.pages||[]).join(', '))}</span></div></article>`).join('')||'<div class="empty">No matching claims in the selected-page sample.</div>'}</div>`;
    detail.scrollIntoView({behavior:'smooth',block:'start'});
  }
  fetch('regional-demo-data.json').then(response=>{if(!response.ok)throw new Error('Could not load regional demo fixture');return response.json();}).then(json=>{data=json;regionView();}).catch(error=>{root.innerHTML=`<div class="empty">${esc(error.message)}. Open this page through the local PolicyTracker preview server.</div>`;});
})();
