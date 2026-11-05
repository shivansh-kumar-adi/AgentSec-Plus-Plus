import {Activity, XCircle} from 'lucide-react'
import {useEffect, useState} from 'react'
import {Navigate, Route, Routes} from 'react-router-dom'
import {API_CONFIGURATION_ERROR} from './api'
import {AuthSession, clearSession, readSession, saveSession} from './auth'
import {Layout} from './components/Layout'
import {ActionHistoryPage} from './pages/ActionHistory'
import {AuditLogsPage} from './pages/AuditLogs'
import {ConfigurationPage} from './pages/Configuration'
import {IncidentsPage} from './pages/Incidents'
import {IntegrationsPage} from './pages/Integrations'
import {InvestigationsPage} from './pages/Investigations'
import {LiveMonitoringPage} from './pages/LiveMonitoring'
import {LoginPage} from './pages/Login'
import {NetworkActivityPage} from './pages/NetworkActivity'
import {NotFoundPage} from './pages/NotFound'
import {OverviewPage} from './pages/Overview'
import {ProcessMonitoringPage} from './pages/ProcessMonitoring'
import {ResponseApprovalsPage} from './pages/ResponseApprovals'
import {SystemHealthPage} from './pages/SystemHealth'
import {ThreatDetectionPage} from './pages/ThreatDetection'

export function App() {
  const [session, setSession] = useState<AuthSession | null>(() => readSession())
  useEffect(() => { const unauthorized = () => { clearSession(); setSession(null) }; window.addEventListener('agentsec:unauthorized', unauthorized); return () => window.removeEventListener('agentsec:unauthorized', unauthorized) }, [])
  const authenticate = (next: AuthSession) => { saveSession(next); setSession(next) }
  const signOut = () => { clearSession(); setSession(null) }
  if (API_CONFIGURATION_ERROR) return <main className="login-shell"><section className="login-brand"><div className="brand-mark"><Activity/></div><span>AGENTSEC / AI</span><h1>Configuration required.</h1><p>The dashboard cannot connect until its production API origin is configured.</p></section><section className="login-card"><div><small>DEPLOYMENT ERROR</small><h2>API unavailable</h2></div><div className="form-error"><XCircle size={16}/>{API_CONFIGURATION_ERROR}</div></section></main>
  if (!session) return <Routes><Route path="/login" element={<LoginPage onAuthenticated={authenticate}/>}/><Route path="*" element={<Navigate to="/login" replace/>}/></Routes>
  return <Routes><Route path="/login" element={<Navigate to="/overview" replace/>}/><Route path="/" element={<Navigate to="/overview" replace/>}/><Route element={<Layout session={session} onSignOut={signOut}/>}><Route path="/overview" element={<OverviewPage/>}/><Route path="/live-monitoring" element={<LiveMonitoringPage/>}/><Route path="/threat-detection" element={<ThreatDetectionPage/>}/><Route path="/incidents" element={<IncidentsPage/>}/><Route path="/investigations" element={<InvestigationsPage/>}/><Route path="/network-activity" element={<NetworkActivityPage/>}/><Route path="/process-monitoring" element={<ProcessMonitoringPage/>}/><Route path="/response-approvals" element={<ResponseApprovalsPage/>}/><Route path="/action-history" element={<ActionHistoryPage/>}/><Route path="/audit-logs" element={<AuditLogsPage/>}/><Route path="/system-health" element={<SystemHealthPage/>}/><Route path="/configuration" element={<ConfigurationPage/>}/><Route path="/integrations" element={<IntegrationsPage/>}/></Route><Route path="*" element={<NotFoundPage/>}/></Routes>
}
