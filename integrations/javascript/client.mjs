/** Small reference client. For private integrations keep service credentials in
 * your backend; browsers call your same-origin backend without a provider key.
 * This does not supply a server, auth flow, inference entitlement or retries.
 */
export class PolicyTrackerError extends Error {
  constructor(status, body) {
    super(body?.message || `PolicyTracker request failed (${status})`);
    this.name = 'PolicyTrackerError';
    this.status = status;
    this.code = body?.code || 'request_failed';
    this.requestId = body?.request_id || null;
  }
}

export class PolicyTrackerClient {
  constructor({ baseUrl, workspaceId, getToken = null, fetchImpl = globalThis.fetch }) {
    if (!baseUrl || !workspaceId || typeof fetchImpl !== 'function') throw new TypeError('baseUrl, workspaceId and fetch are required');
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.workspaceId = workspaceId;
    this.getToken = getToken;
    this.fetch = fetchImpl;
  }
  async request(method, path, { query = {}, body, etag, idempotencyKey, ifMatch, signal } = {}) {
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== '') search.set(key, Array.isArray(value) ? value.join(',') : String(value));
    }
    const suffix = search.size ? `?${search}` : '';
    const headers = { Accept: 'application/json' };
    if (this.getToken) {
      const token = await this.getToken();
      if (!token) throw new Error('No authenticated service token; no anonymous fallback');
      headers.Authorization = `Bearer ${token}`;
    }
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (etag) headers['If-None-Match'] = etag;
    if (ifMatch) headers['If-Match'] = ifMatch;
    if (idempotencyKey) headers['Idempotency-Key'] = idempotencyKey;
    const url = `${this.baseUrl}/v1/workspaces/${encodeURIComponent(this.workspaceId)}${path}${suffix}`;
    const response = await this.fetch(url, { method, headers, body: body === undefined ? undefined : JSON.stringify(body), signal });
    if (response.status === 304) return { status: 304, data: null, etag: response.headers.get('ETag') };
    let data;
    try { data = await response.json(); } catch { throw new PolicyTrackerError(response.status, { code: 'invalid_response', message: 'Expected a JSON API response' }); }
    if (!response.ok) throw new PolicyTrackerError(response.status, data);
    return { status: response.status, data, etag: response.headers.get('ETag') };
  }
  getPrime(countryCode, options = {}) { return this.request('GET', `/countries/${encodeURIComponent(countryCode)}/prime`, options); }
  getDashboard(bundleId, options = {}) { return this.request('GET', `/bundles/${encodeURIComponent(bundleId)}/dashboard`, options); }
  queryRecords(bundleId, query = {}, options = {}) { return this.request('GET', `/bundles/${encodeURIComponent(bundleId)}/records`, { ...options, query }); }
  getEvidence(bundleId, evidenceId, options = {}) { return this.request('GET', `/bundles/${encodeURIComponent(bundleId)}/evidence/${encodeURIComponent(evidenceId)}`, options); }
  startRun(submission, { idempotencyKey, signal } = {}) {
    if (!idempotencyKey) throw new TypeError('An idempotency key is required for a potentially billable run');
    return this.request('POST', '/runs', { body: submission, idempotencyKey, signal });
  }
  selectPrime(countryCode, selection, { ifMatch, signal } = {}) {
    if (!ifMatch) throw new TypeError('Current pointer ETag is required');
    return this.request('PUT', `/countries/${encodeURIComponent(countryCode)}/prime`, { body: selection, ifMatch, signal });
  }
}
