export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

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
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username, password}),
  })
  if (!response.ok) throw new Error('Invalid credentials')
  return response.json() as Promise<{access_token: string; user: {username: string; role: string}}>
}

export async function api<T>(path: string, token: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...options?.headers},
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail ?? `Request failed (${response.status})`)
  }
  return response.json()
}

