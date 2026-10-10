const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function settingsPage(data,topics,countries,target){
  if(!data)return '<h1>Method & output settings</h1><p role="status">Loading saved settings…</p>';
  const s=data.settings;
  return `<h1>Method & output settings</h1><p class="muted">Save defaults for future runs, or save and regenerate now. Published versions keep their original method.</p><form id="settings-form" class="paper settings-form">
    <div class="settings-columns"><label>Report language<input name="output_language" aria-label="Report language" value="${esc(s.output_language)}" maxlength="80"></label><label>Level of detail<select name="detail" aria-label="Level of detail">${['concise','standard','detailed'].map(x=>`<option ${s.detail===x?'selected':''}>${x}</option>`).join('')}</select></label></div>
    <label>What should the analysis focus on?<textarea name="instructions" aria-label="Analysis instructions" rows="4" maxlength="8000" placeholder="For example: explain financing conditions and responsibilities in plain language.">${esc(s.instructions)}</textarea></label>
    <details><summary>Topics · ${s.topic_ids.length||'all'}</summary><p>Focus extraction on these topics. Leave all unchecked to cover the full method.</p><div class="settings-topics">${topics.map(t=>`<label><input type="checkbox" name="topic_ids" value="${esc(t.id)}" ${s.topic_ids.includes(t.id)?'checked':''}>${esc(t.name||t.label)}</label>`).join('')}</div></details>
    <label>Terminology and translation preferences<textarea name="glossary" aria-label="Terminology" rows="3" maxlength="8000" placeholder="Preferred translations, acronyms or terminology">${esc(s.glossary)}</textarea></label>
    <details><summary>Processing options</summary><label><input type="checkbox" name="vision_recovery" ${s.vision_recovery?'checked':''}> Use the connected model to read difficult page images</label><label>OCR languages<input name="ocr_languages" aria-label="OCR languages" value="${esc(s.ocr_languages)}" placeholder="auto"></label><p class="small-note">Auto uses installed languages. Image recovery uses the selected AI connection; originals remain unchanged.</p><label>Automatic connection retries<input name="retry_limit" aria-label="Automatic connection retries" type="number" min="0" max="3" value="${s.retry_limit}"></label></details>
    <div class="settings-columns"><label>${target?.draft?'Rerun the current analysis':'Country to regenerate'}<select name="rerun_country" aria-label="Country to regenerate" ${target?.draft?'disabled':''}>${countries.filter(c=>c.document_count).map(c=>`<option value="${c.code}" ${(target?.country||'ALB')===c.code?'selected':''}>${esc(c.name)}</option>`).join('')}</select></label></div>
    <div class="inline-actions"><button type="submit" class="primary" id="settings-save">Save settings</button><button type="button" id="settings-rerun" ${!target?.draft&&!countries.some(c=>c.document_count)?'disabled':''}>Save & rerun</button></div><p id="settings-status" role="status"></p>
    <details><summary>Previous settings</summary>${data.history.map(h=>`<p>${esc(h.language)} · ${esc(h.detail)} <button type="button" data-restore-settings="${esc(h.id)}">Restore ${esc(h.version)}</button></p>`).join('')||'<p>No earlier saved settings.</p>'}</details></form>`;
}

export function settingsFromForm(form,current){
  const values=new FormData(form);
  return {...current,output_language:values.get('output_language'),detail:values.get('detail'),instructions:values.get('instructions'),
    glossary:values.get('glossary'),topic_ids:values.getAll('topic_ids'),ocr_languages:values.get('ocr_languages'),
    vision_recovery:values.has('vision_recovery'),retry_limit:Number(values.get('retry_limit'))};
}
