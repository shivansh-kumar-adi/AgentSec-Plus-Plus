export type AuthSession = {token: string; username: string; role: string}
const keys = {token: 'agentsec_token', username: 'agentsec_identity', role: 'agentsec_role'} as const
export function readSession(): AuthSession | null { const token = sessionStorage.getItem(keys.token); const username = sessionStorage.getItem(keys.username); const role = sessionStorage.getItem(keys.role); return token && username && role ? {token, username, role} : null }
export function saveSession(session: AuthSession): void { sessionStorage.setItem(keys.token, session.token); sessionStorage.setItem(keys.username, session.username); sessionStorage.setItem(keys.role, session.role) }
export function clearSession(): void { Object.values(keys).forEach(key => sessionStorage.removeItem(key)) }
