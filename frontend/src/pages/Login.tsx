import {FormEvent, useState} from 'react'
import {Activity, KeyRound, XCircle} from 'lucide-react'
import {login} from '../api'
import {AuthSession} from '../auth'

export function LoginPage({onAuthenticated}: {onAuthenticated: (session: AuthSession) => void}) {
  const [username, setUsername] = useState(''); const [password, setPassword] = useState(''); const [error, setError] = useState(''); const [submitting, setSubmitting] = useState(false)
  const submit = async (event: FormEvent) => { event.preventDefault(); setError(''); setSubmitting(true); try { const result = await login(username, password); onAuthenticated({token: result.access_token, username: result.user.username, role: result.user.role}) } catch (reason) { setError(reason instanceof Error ? reason.message : 'Login failed') } finally { setSubmitting(false) } }
  return <main className="login-shell"><section className="login-brand"><div className="brand-mark"><Activity/></div><span>AGENTSEC / AI</span><h1>Defense begins with evidence.</h1><p>An operational workspace for endpoint telemetry, explainable investigations, and controlled response.</p><div className="signal"><span/> Backend authentication required</div></section><form className="login-card" onSubmit={submit}><div><small>SECURE CONSOLE</small><h2>Operator sign in</h2><p>Use credentials configured on the backend.</p></div><label>Username<input autoComplete="username" value={username} onChange={event => setUsername(event.target.value)} required/></label><label>Password<input type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} required/></label>{error && <div className="form-error"><XCircle size={16}/>{error}</div>}<button disabled={submitting}><KeyRound size={16}/>{submitting ? 'Authenticating…' : 'Authenticate'}</button></form></main>
}
