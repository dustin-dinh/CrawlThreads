const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {headers: {'Content-Type': 'application/json', ...(options?.headers || {})}, ...options})
  if (!response.ok) {
    const body = await response.json().catch(() => ({detail: response.statusText}))
    throw new Error(body.detail || `HTTP ${response.status}`)
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, {method:'POST', body: body === undefined ? undefined : JSON.stringify(body)}),
  patch: <T>(path: string, body?: unknown) => request<T>(path, {method:'PATCH', body: body === undefined ? undefined : JSON.stringify(body)}),
  delete: <T>(path: string) => request<T>(path, {method:'DELETE'})
}
