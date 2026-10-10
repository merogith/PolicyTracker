import {projectDashboard,defaultView,validateView} from './evidence-model.mjs';
/** Data-only source-record component. No network, inference or archive mutations. */
class PolicyTracker extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._data = null;
    this._query = '';
  }
  set data(value) {
    if (!value || typeof value.release_id !== 'string' || !Array.isArray(value.rows) || !value.rows.every(r => typeof r.label_en === 'string' && Array.isArray(r.evidence_ids))) {
      throw new TypeError('Expected a dashboard projection with release_id and rows');
    }
    this._data = value;
    this.render();
  }
  get data() { return this._data; }
  set profile(value) { const view=this._view||defaultView(value); const errors=validateView(value,view); if(errors.length)throw new TypeError(errors.join(' ')); this.data=projectDashboard(value,view); this._profile=value; }
  set view(value) { if(this._profile){const errors=validateView(this._profile,value);if(errors.length)throw new TypeError(errors.join(' '));this.data=projectDashboard(this._profile,value);}this._view=value; }
  connectedCallback() { this.render(); }
  element(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }
  render() {
    const style = document.createElement('style');
    style.textContent = `
      :host{display:block;color:var(--pt-text,#182b36);font:400 14px/1.55 system-ui,sans-serif}
      *{box-sizing:border-box} .bar{display:flex;gap:12px;align-items:end;justify-content:space-between;flex-wrap:wrap;margin-bottom:18px}
      label{display:grid;gap:5px;font-size:12px;color:var(--pt-muted,#4c6270)}input{min-height:44px;width:min(100%,320px);padding:10px 12px;border:1px solid var(--pt-border,#cbd5dc);border-radius:7px;font:inherit;color:inherit;background:var(--pt-surface,#fff)}
      button{min-height:44px;border:1px solid var(--pt-border,#cbd5dc);border-radius:6px;background:var(--pt-surface,#fff);color:var(--pt-accent,#006b68);padding:8px 12px;font:600 13px system-ui;cursor:pointer}
      :focus-visible{outline:3px solid var(--pt-accent,#006b68);outline-offset:3px}.scroll{overflow:auto;border:1px solid var(--pt-border,#dce4e8);border-radius:9px}
      table{border-collapse:collapse;width:100%;min-width:620px;text-align:left;background:var(--pt-surface,#fff)}th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--pt-muted,#4c6270);background:var(--pt-soft,#f5f8fa)}th,td{padding:15px;border-bottom:1px solid var(--pt-border,#dce4e8)}tr:last-child td{border-bottom:0}th:first-child{width:32%}
      .sub{color:var(--pt-muted,#4c6270);font-size:12px;margin-top:5px}.count{font-size:12px;color:var(--pt-muted,#4c6270)}.empty{padding:22px;background:var(--pt-soft,#f5f8fa);border-radius:8px}
      @media(max-width:600px){.bar label{width:100%}input{width:100%;font-size:16px}}
    `;
    this.shadowRoot.replaceChildren(style);
    if (!this._data) { this.shadowRoot.append(this.element('p', 'Choose a report to view its source records.', 'empty')); return; }
    const bar = this.element('div', undefined, 'bar');
    const label = this.element('label', 'Search this loaded view');
    const input = this.element('input'); input.type = 'search'; input.placeholder = 'Action, target or hazard'; input.value = this._query;
    label.append(input); bar.append(label);
    const count = this.element('div', '', 'count'); count.setAttribute('aria-live','polite'); bar.append(count);
    const wrap = this.element('div', undefined, 'scroll');
    wrap.tabIndex=0; wrap.setAttribute('role','region'); wrap.setAttribute('aria-label','Scrollable source-record table');
    const table = this.element('table'); table.setAttribute('aria-label','Source records from the selected report');
    const head = this.element('thead'); const header = this.element('tr');
    ['Statement','Target and condition','Risk lens','Evidence'].forEach(x => { const cell=this.element('th',x); cell.scope='col'; header.append(cell); }); head.append(header); table.append(head);
    const tbody = this.element('tbody'); table.append(tbody); wrap.append(table);
    const empty = this.element('p', 'No records match this view. Change the search; this does not mean no national policy exists.', 'empty'); empty.hidden=true;
    const update = () => {
      const query = this._query.toLocaleLowerCase();
      const rows = this._data.rows.filter(r => [r.label_en,r.target_display,...(r.hazards||[])].join(' ').toLocaleLowerCase().includes(query));
      count.textContent = `${rows.length} of ${this._data.rows.length} ${this._data.count_unit==='source_records'?'source records':'loaded records (legacy projection)'} · ${this._data.release_id}`;
      tbody.replaceChildren(); empty.hidden=rows.length>0; wrap.hidden=rows.length===0;
      for (const row of rows) {
        const tr = this.element('tr');
        const labelCell=this.element('td'); labelCell.append(this.element('strong',row.label_en),this.element('div',(row.topic_ids||[]).join(' · '),'sub'));
        const target=this.element('td',row.target_display||'No quantitative target stated'); target.append(this.element('div','Performance not assessed','sub'));
        const risk=this.element('td',(row.hazards||[]).join(', ')||'Not specified'); risk.append(this.element('div',(row.risk_functions||row.drr_phases||[]).map(x=>x.replaceAll('_',' ')).join(', '),'sub'));
        const actions=this.element('td'); const button=this.element('button','View source'); button.type='button'; button.disabled=!row.evidence_ids.length;
        button.addEventListener('click',()=>this.dispatchEvent(new CustomEvent('evidenceopen',{bubbles:true,composed:true,detail:{releaseId:this._data.release_id,evidenceId:row.evidence_ids[0],evidenceIds:row.evidence_ids,recordId:row.record_id||row.commitment_id,commitmentId:row.commitment_id}})));
        actions.append(button); tr.append(labelCell,target,risk,actions); tbody.append(tr);
      }
    };
    input.addEventListener('input',()=>{this._query=input.value;update();});
    this.shadowRoot.append(bar,wrap,empty); update();
  }
}
if (!customElements.get('policy-tracker')) customElements.define('policy-tracker',PolicyTracker);
