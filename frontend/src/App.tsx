import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Activity, Bot, CheckCircle2, ClipboardCheck, FileClock, Gauge, KeyRound,
  LayoutDashboard, ListFilter, Network, Plug, Radio, Search, Settings, ShieldAlert,
  Siren, TerminalSquare, Users, XCircle } from 'lucide-react'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ActionRecord, api, EventRecord, Incident, login } from './api'

const pages = [
  ['Overview', LayoutDashboard], ['Live monitoring', Radio], ['Threat detection', ShieldAlert],
  ['Incident management', Siren], ['AI investigation', Bot], ['Network activity', Network],
  ['Process monitoring', TerminalSquare], ['Response approvals', ClipboardCheck],
  ['Action history', FileClock], ['Audit logs', ListFilter], ['System health', Gauge],
  ['Configuration', Settings], ['Integrations', Plug],
] as const

function severityLabel(value: number) {
  if (value >= 9) return 'Critical'
  if (value >= 7) return 'High'
  if (value >= 4) return 'Medium'
  return 'Low'
}

function Login({onAuthenticated}: {onAuthenticated: (token: string, user: string, role: string) => void}) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError('')
    try { const result = await login(username, password); onAuthenticated(result.access_token, result.user.username, result.user.role) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Login failed') }
  }
  return <main className="login-shell">
    <section className="login-brand"><div className="brand-mark"><Activity /></div><span>AGENTSEC / AI</span>
      <h1>Defense begins with evidence.</h1><p>A local-first security operations workspace for monitored endpoints, explainable investigations, and controlled response.</p>
      <div className="signal"><span></span> Backend authentication required</div>
    </section>
    <form className="login-card" onSubmit={submit}><div><small>SECURE CONSOLE</small><h2>Operator sign in</h2><p>Use credentials configured on the backend.</p></div>
      <label>Username<input autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} required /></label>
      <label>Password<input type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required /></label>
      {error && <div className="form-error"><XCircle size={16}/>{error}</div>}<button><KeyRound size={16}/> Authenticate</button>
    </form>
  </main>
}

export function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem('agentsec_token') ?? '')
  const [identity, setIdentity] = useState(() => sessionStorage.getItem('agentsec_identity') ?? '')
  const [role, setRole] = useState(() => sessionStorage.getItem('agentsec_role') ?? '')
  const [page, setPage] = useState('Overview')
  const [events, setEvents] = useState<EventRecord[]>([])
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [actions, setActions] = useState<ActionRecord[]>([])
  const [error, setError] = useState('')
  const authenticate = (value: string, user: string, nextRole: string) => {
    sessionStorage.setItem('agentsec_token', value); sessionStorage.setItem('agentsec_identity', user)
    sessionStorage.setItem('agentsec_role', nextRole); setToken(value); setIdentity(user); setRole(nextRole)
  }
  useEffect(() => {
    if (!token) return
    Promise.all([api<EventRecord[]>('/api/v1/events?limit=250', token), api<Incident[]>('/api/v1/incidents', token), api<ActionRecord[]>('/api/v1/actions', token)])
      .then(([nextEvents, nextIncidents, nextActions]) => {setEvents(nextEvents); setIncidents(nextIncidents); setActions(nextActions)})
      .catch(reason => setError(reason.message))
  }, [token])
  const timeline = useMemo(() => {
    const points = new Map<string, number>()
    events.forEach(item => { const key = new Date(item.occurred_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}); points.set(key, (points.get(key) ?? 0) + 1) })
    return [...points].reverse().slice(-16).map(([time, count]) => ({time, count}))
  }, [events])
  if (!token) return <Login onAuthenticated={authenticate}/>
  const critical = incidents.filter(item => item.severity >= 9 && item.status === 'open').length
  const open = incidents.filter(item => item.status === 'open').length
  const pending = actions.filter(item => item.status === 'pending').length
  return <div className="app-shell"><aside><div className="logo"><Activity/><span>AGENTSEC <b>AI</b></span></div><nav>{pages.map(([label, Icon]) =>
    <button key={label} className={page === label ? 'active' : ''} onClick={() => setPage(label)}><Icon size={17}/><span>{label}</span>{label === 'Response approvals' && pending > 0 && <i>{pending}</i>}</button>)}</nav>
    <div className="operator"><div>{identity.slice(0,2).toUpperCase()}</div><span><b>{identity}</b><small>{role}</small></span><button aria-label="Sign out" onClick={() => {sessionStorage.clear(); setToken('')}}>↗</button></div>
  </aside><main className="workspace"><header><div><small>SECURITY OPERATIONS / {page.toUpperCase()}</small><h1>{page}</h1></div><div className="header-tools"><label><Search size={16}/><input placeholder="Filter telemetry"/></label><span className="health"><i></i>API connected</span></div></header>
    {error && <div className="banner"><XCircle size={16}/>{error}</div>}
    <section className="metrics"><Metric label="Open incidents" value={open} detail="Requires analyst review" tone="amber"/><Metric label="Critical" value={critical} detail="Severity 9–10" tone="red"/><Metric label="Events retained" value={events.length} detail="Current API window" tone="blue"/><Metric label="Pending approvals" value={pending} detail="No automatic execution" tone="green"/></section>
    <section className="grid"><article className="panel chart-panel"><PanelTitle title="Telemetry cadence" subtitle="Events received from registered agents"/><div className="chart">
      {timeline.length ? <ResponsiveContainer width="100%" height="100%"><AreaChart data={timeline}><defs><linearGradient id="eventFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#5eead4" stopOpacity={.4}/><stop offset="1" stopColor="#5eead4" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#202a39" vertical={false}/><XAxis dataKey="time" stroke="#738096" tickLine={false}/><YAxis stroke="#738096" allowDecimals={false} tickLine={false}/><Tooltip contentStyle={{background:'#111927',border:'1px solid #29364a'}}/><Area dataKey="count" stroke="#5eead4" fill="url(#eventFill)" strokeWidth={2}/></AreaChart></ResponsiveContainer> : <Empty text="No telemetry received yet"/>}
    </div></article><article className="panel"><PanelTitle title="Incident pressure" subtitle="Actual incident records by severity"/><div className="severity-stack">{[10,9,8,7,6,5,4,3,2,1,0].map(level => incidents.some(x => x.severity === level) && <div key={level}><span>{severityLabel(level)} / {level}</span><b style={{width: `${Math.max(8, incidents.filter(x => x.severity === level).length / Math.max(1, incidents.length) * 100)}%`}}></b><em>{incidents.filter(x => x.severity === level).length}</em></div>)}{!incidents.length && <Empty text="No incidents created"/>}</div></article></section>
    <section className="panel table-panel"><PanelTitle title="Latest security events" subtitle="Normalized endpoint data; no seeded records"/><div className="table-wrap"><table><thead><tr><th>Severity</th><th>Event</th><th>Source</th><th>Description</th><th>Observed</th></tr></thead><tbody>{events.slice(0,12).map(item => <tr key={item.id}><td><span className={`pill s${Math.min(9,item.severity)}`}>{severityLabel(item.severity)} {item.severity}</span></td><td>{item.event_type.replaceAll('_',' ')}</td><td className="mono">{item.source_ip ?? (item.process_id ? `PID ${item.process_id}` : 'local')}</td><td>{item.description}</td><td>{new Date(item.occurred_at).toLocaleString()}</td></tr>)}</tbody></table>{!events.length && <Empty text="Install and enroll a local agent to begin monitoring"/>}</div></section>
  </main></div>
}

function Metric({label,value,detail,tone}:{label:string,value:number,detail:string,tone:string}) { return <article className={`metric ${tone}`}><small>{label}</small><strong>{value}</strong><span>{detail}</span></article> }
function PanelTitle({title,subtitle}:{title:string,subtitle:string}) { return <div className="panel-title"><div><h2>{title}</h2><p>{subtitle}</p></div><button><ListFilter size={16}/> Filter</button></div> }
function Empty({text}:{text:string}) { return <div className="empty"><CheckCircle2 size={22}/><span>{text}</span></div> }

