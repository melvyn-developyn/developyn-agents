export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function api(path: string, opts: RequestInit = {}): Promise<any> {
  const res = await fetch('/api' + path, {
    credentials: 'include',
    ...opts,
    headers: opts.body ? { 'Content-Type': 'application/json', ...(opts.headers ?? {}) } : opts.headers,
  });
  if (res.status === 204) return null;
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const j = await res.json();
      msg = j.error ?? msg;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, msg);
  }
  const ct = res.headers.get('content-type') ?? '';
  return ct.includes('application/json') ? res.json() : res.text();
}
