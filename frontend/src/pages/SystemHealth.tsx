import {useCallback} from 'react'
import {useOutletContext} from 'react-router-dom'
import {AuthSession} from '../auth'
import {fetchEvents, fetchHealth} from '../api'
import {ErrorState, LoadingState, Notice, PageHeader, RefreshButton, StatCard, StatusBadge} from '../components/common'
import {useResource} from '../hooks/useResource'

export function SystemHealthPage() {
  const {token} = useOutletContext<AuthSession>(); const loader = useCallback(async () => { const [health, events] = await Promise.all([fetchHealth(), fetchEvents(token)]); return {health, events} }, [token]); const state = useResource(loader, 20_000)
  if (state.loading) return <LoadingState label="Checking service health"/>
  if (state.error || !state.data) return <><PageHeader eyebrow="SERVICE RELIABILITY" title="System Health" description="Backend and database availability."/><ErrorState message={state.error} retry={state.refresh}/></>
  const agents = new Map<string, string>(); state.data.events.forEach(event => { if (!agents.has(event.agent_id) || event.received_at > agents.get(event.agent_id)!) agents.set(event.agent_id, event.received_at) })
  return <><PageHeader eyebrow="SERVICE RELIABILITY" title="System Health" description="Live backend checks and observed endpoint activity." actions={<RefreshButton onClick={state.refresh} updatedAt={state.updatedAt}/>}/><section className="stat-grid"><StatCard label="Backend API" value={<StatusBadge value={state.data.health.status}/>} detail="GET /health" tone="green"/><StatCard label="Database" value={<StatusBadge value={state.data.health.database}/>} detail="Backend connectivity check" tone="green"/><StatCard label="Observed agents" value={agents.size} detail="Distinct agents in event window"/><StatCard label="Last refresh" value={state.updatedAt?.toLocaleTimeString() ?? '—'} detail="Automatic refresh every 20 seconds"/></section><section className="panel"><div className="panel-heading"><div><h2>Observed agent activity</h2><p>This is telemetry-derived status, not the agent registry.</p></div></div>{agents.size ? <div className="compact-list">{[...agents].map(([id, last]) => <div key={id}><StatusBadge value="observed"/><span><b className="mono">{id}</b><small>Last event received {new Date(last).toLocaleString()}</small></span></div>)}</div> : <Notice title="No observable agent activity">The backend has no agent-list endpoint and the current event window contains no agents.</Notice>}</section></>
}
