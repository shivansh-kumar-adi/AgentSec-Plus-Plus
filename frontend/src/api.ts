const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()

export const API_CONFIGURATION_ERROR = !configuredApiBaseUrl && !import.meta.env.DEV
  ? 'Frontend configuration error: VITE_API_BASE_URL is required in production.'
  : null

export function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, '')
}

export const API_BASE_URL = normalizeBaseUrl(configuredApiBaseUrl || (import.meta.env.DEV ? 'http://localhost:8000' : ''))
export type JsonValue = string | number | boolean | null | JsonValue[] | {[key: string]: JsonValue}
export type EventRecord = {id: number; agent_id: string; event_id: string; event_type: 'process' | 'network_connection' | 'authentication' | 'file_change' | 'detection'; occurred_at: string; received_at: string; severity: number; source_ip?: string | null; process_id?: number | null; username?: string | null; description: string; attributes_json: string; attributes: Record<string, JsonValue>}
export type Incident = {id: number; title: string; status: string; severity: number; category: string; summary: string; created_at: string; updated_at: string}
export type Investigation = {id: number; incident_id: number; classification: string; severity: number; evidence: Array<{event_id: number; type: string; severity: number; occurred_at: string}>; explanation: string; recommendations: string[]; provider: string}
export type ActionRecord = {id: number; incident_id: number; action_type: string; target: string; parameters_json: string; status: string; simulation: number; requested_by: number; approved_by?: number | null; requested_at: string; decided_at?: string | null; executed_at?: string | null; result_json?: string | null}
export type AuditRecord = {id: number; actor_type: string; actor_id: string; action: string; resource_type: string; resource_id?: string | null; details_json: string; created_at: string}
export type HealthStatus = {status: string; database: string}
export type LoginResult = {access_token: string; token_type: string; user: {id: number; username: string; role: string}}

export class ApiError extends Error { constructor(message: string, public status?: number) { super(message) } }

function apiUrl(path: string): string {
  if (API_CONFIGURATION_ERROR) throw new ApiError(API_CONFIGURATION_ERROR)
  return `${API_BASE_URL}${path}`
}

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 15_000)
  try {
    const response = await fetch(apiUrl(path), {...options, signal: controller.signal, headers: {'Content-Type': 'application/json', ...(token ? {Authorization: `Bearer ${token}`} : {}), ...options.headers}})
    if (!response.ok) {
      const body = await response.json().catch(() => ({})) as {detail?: string}
      if (response.status === 401 && token) window.dispatchEvent(new Event('agentsec:unauthorized'))
      throw new ApiError(body.detail ?? `Request failed (${response.status})`, response.status)
    }
    return response.json() as Promise<T>
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw new ApiError('The API request timed out.')
    throw error
  } finally { window.clearTimeout(timeout) }
}

export function login(username: string, password: string) { return request<LoginResult>('/api/v1/auth/login', {method: 'POST', body: JSON.stringify({username, password})}) }
export function fetchHealth() { return request<HealthStatus>('/health') }
export function fetchEvents(token: string, eventType?: string, limit = 500) { const query = new URLSearchParams({limit: String(limit)}); if (eventType) query.set('event_type', eventType); return request<EventRecord[]>(`/api/v1/events?${query}`, {}, token) }
export function fetchIncidents(token: string) { return request<Incident[]>('/api/v1/incidents', {}, token) }
export function fetchActions(token: string) { return request<ActionRecord[]>('/api/v1/actions', {}, token) }
export function fetchAudit(token: string) { return request<AuditRecord[]>('/api/v1/audit', {}, token) }
export function createInvestigation(token: string, incidentId: number) { return request<Investigation>('/api/v1/investigations', {method: 'POST', body: JSON.stringify({incident_id: incidentId})}, token) }
export function approveAction(token: string, actionId: number) { return request<{id: number; status: string; result: Record<string, JsonValue>}>(`/api/v1/actions/${actionId}/approve`, {method: 'POST'}, token) }
