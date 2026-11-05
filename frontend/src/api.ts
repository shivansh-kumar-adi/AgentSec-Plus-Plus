const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()

export const API_CONFIGURATION_ERROR = !configuredApiBaseUrl && !import.meta.env.DEV
  ? 'Frontend configuration error: VITE_API_BASE_URL is required in production.'
  : null

export const API_BASE_URL = (configuredApiBaseUrl || (import.meta.env.DEV ? 'http://localhost:8000' : ''))
  .replace(/\/+$/, '')

function apiUrl(path: string): string {
  if (API_CONFIGURATION_ERROR) throw new Error(API_CONFIGURATION_ERROR)
  return `${API_BASE_URL}${path}`
}

export type EventRecord = {
  id: number; agent_id: string; event_type: string; occurred_at: string;
  severity: number; source_ip?: string; process_id?: number; description: string;
}
export type Incident = {
  id: number; title: string; status: string; severity: number; category: string;
  summary: string; created_at: string;
}
export type ActionRecord = {
  id: number; incident_id: number; action_type: string; target: string;
  status: string; simulation: number; requested_at: string;
}

export async function login(username: string, password: string) {
  const response = await fetch(apiUrl('/api/v1/auth/login'), {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username, password}),
  })
  if (!response.ok) throw new Error('Invalid credentials')
  return response.json() as Promise<{access_token: string; user: {username: string; role: string}}>
}

export async function api<T>(path: string, token: string, options?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...options,
    headers: {'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...options?.headers},
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail ?? `Request failed (${response.status})`)
  }
  return response.json()
}

