export const ROUTES = {codex_chatgpt:'ChatGPT plan',openai_api:'OpenAI API'};
export const effortLabel = value => ({default:'Model default',none:'None',minimal:'Minimal',low:'Low',medium:'Medium',high:'High',xhigh:'Extra high',max:'Maximum',ultra:'Ultra'}[value] || value);
export const initialSelection = () => ({route:'codex_chatgpt',model:'gpt-6-astra',effort:'xhigh'});
export function selectionProblem(selection, status) {
  if (!status) return 'Connect an account to load available models.';
  if (!(selection.route === 'codex_chatgpt' ? status.chatgpt?.connected : status.api?.connected)) return `Connect ${ROUTES[selection.route] || 'a usage route'} to continue.`;
  const model = status.models?.[selection.route]?.find(m => m.id === selection.model);
  if (!model) return 'Choose a model from the refreshed catalog. Your previous selection has been kept.';
  if (!model.efforts.includes(selection.effort)) return 'Choose a supported reasoning effort for this model.';
  return '';
}
export function selectModel(selection, model) {
  return {...selection,model:model.id,effort:model.efforts.includes(selection.effort) ? selection.effort : model.default_effort};
}
export function usageWindows(data) {
  return (data?.buckets || []).flatMap(bucket => ['primary','secondary'].flatMap(key => {
    const window=bucket[key];
    if (!window || typeof window.usedPercent !== 'number') return [];
    return [{name:bucket.limitName || bucket.limitId || 'ChatGPT',...window,remaining:Math.max(0,Math.min(100,100-window.usedPercent))}];
  }));
}
export class AIClient {
  constructor(fetcher=globalThis.fetch?.bind(globalThis)) { this.fetcher=fetcher;this.csrf=null; }
  async request(path,body) {
    const controller=new AbortController();
    // A cold full-document scan can take minutes; OCR can render and recognize
    // a page for up to three minutes each. These local actions do not call AI.
    // Never retry this write after a timeout: a draft may already have been saved.
    const timer=setTimeout(()=>controller.abort(),path==='/preparation'?390000:105000);
    try {
      // A dropped status read is safe to retry once. Never repeat a write: the
      // server may already have accepted it, including a billable model request.
      for(let attempt=0;attempt<2;attempt++) {
        try {
          const response=await this.fetcher('/api/ai'+path,{method:body===undefined?'GET':'POST',credentials:'same-origin',cache:'no-store',signal:controller.signal,
            headers:body===undefined?{}:{'Content-Type':'application/json','X-PolicyTracker-CSRF':this.csrf || ''},body:body===undefined?undefined:JSON.stringify(body)});
          let data;try {data=await response.json();}catch(error) {
            if(error instanceof TypeError||error.name==='AbortError')throw error;
            throw new Error('Start the local AI server with Python 3.10+: python scripts/preview_ui.py');
          }
          if (!response.ok) {
            // Saved results remain readable after a local server/session restart.
            // Renew only for a read; never replay an execution or other write.
            if(body===undefined&&path!=='/session'&&attempt===0&&data.error?.code==='session_expired'){
              await this.session();continue;
            }
            const error=new Error(data.error?.message || 'Could not complete the request.');error.code=data.error?.code;throw error;
          }
          return data;
        } catch(error) {if(body!==undefined||attempt>0||!(error instanceof TypeError))throw error;}
      }
    } catch(error) {if(error.name==='AbortError')throw new Error('The connection timed out. Refresh and try again.');throw error;}
    finally {clearTimeout(timer);}
  }
  async session() {
    if(!this.pendingSession)this.pendingSession=this.request('/session').then(data=>{this.csrf=data.csrf;return data;}).finally(()=>{this.pendingSession=null;});
    return this.pendingSession;
  }
  async init() {await this.session();return this.request('/status');}
}
