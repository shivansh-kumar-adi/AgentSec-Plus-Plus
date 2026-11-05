import {Activity, Bot, ClipboardCheck, FileClock, Gauge, LayoutDashboard, ListFilter, Network, Plug, Radio, Settings, ShieldAlert, Siren, TerminalSquare} from 'lucide-react'
import {NavLink, Outlet} from 'react-router-dom'
import {AuthSession} from '../auth'
import {routeDefinitions} from '../routes/routeConfig'

const icons = {overview: LayoutDashboard, live: Radio, threat: ShieldAlert, incidents: Siren, investigations: Bot, network: Network, process: TerminalSquare, approvals: ClipboardCheck, history: FileClock, audit: ListFilter, health: Gauge, configuration: Settings, integrations: Plug}
export function Layout({session, onSignOut}: {session: AuthSession; onSignOut: () => void}) { return <div className="app-shell"><aside className="sidebar"><div className="logo"><Activity/><span>AGENTSEC <b>AI</b></span></div><nav>{routeDefinitions.map(item => { const Icon = icons[item.icon]; return <NavLink key={item.path} to={item.path} className={({isActive}) => isActive ? 'active' : ''}><Icon size={17}/><span>{item.label}</span></NavLink> })}</nav><div className="operator"><div>{session.username.slice(0, 2).toUpperCase()}</div><span><b>{session.username}</b><small>{session.role}</small></span><button aria-label="Sign out" onClick={onSignOut}>↗</button></div></aside><main className="workspace"><Outlet context={session}/></main></div> }
