# AgentSec AI Architecture

## High-level system architecture

```mermaid
flowchart TB
  subgraph Host[Windows monitored host]
    P[Process table] --> C[C++17 collector]
    N[IPv4 TCP table] --> C
    C -->|JSON Lines| U[Python uploader]
  end
  U -->|Signed POST /api/v1/events| API[FastAPI control plane]
  subgraph Control[Backend services]
    API --> AUTH[Operator auth and RBAC]
    API --> VERIFY[Agent HMAC, timestamp and nonce validation]
    API --> LIMIT[Per-agent event rate limiter]
    API --> POLICY[Deterministic investigation policy]
    API --> APPROVAL[Response approval workflow]
    API --> STREAM[WebSocket broadcaster]
  end
  API --> DB[(SQLite local or PostgreSQL production)]
  API --> AUDIT[(Audit records)]
  STREAM --> UI[React SOC dashboard]
  UI -->|Bearer-authenticated REST| API
```

## Component responsibilities

| Component | Responsibility |
|---|---|
| React dashboard | Authenticates operators and displays API-backed events, incidents, actions, status and charts. |
| FastAPI backend | Validates identities and payloads, persists records, creates incidents, coordinates investigations/actions, streams event summaries. |
| Authentication/RBAC | PBKDF2 password verification; HMAC-signed one-hour tokens; `admin`, `analyst`, and `viewer` route gates. |
| Agent registration | Admin-only issuance of UUID and one-time signing material. Only `POST /api/v1/agents` exists. |
| C++ collector | Uses Toolhelp process snapshots and `GetTcpTable2`; emits normalized JSONL. |
| Python uploader | Runs the collector, compacts JSON and signs/sends each event independently. |
| SQLite/PostgreSQL | Stores users, agents, nonces, events, incidents, investigations, actions and audit records. |
| Investigation policy | Deterministically classifies linked evidence and generates bounded recommendations. |
| Response workflow | Records requests and admin approvals; verified execution is simulation only. |

## Endpoint event-ingestion sequence

```mermaid
sequenceDiagram
  participant W as Windows APIs
  participant C as C++ collector
  participant U as Python uploader
  participant B as FastAPI backend
  participant D as configured database
  participant S as WebSocket clients
  W->>C: Process and IPv4 TCP snapshots
  C-->>U: One JSON event per line
  U->>U: Compact JSON and SHA-256 body hash
  U->>U: HMAC(timestamp + nonce + body hash)
  U->>B: POST /api/v1/events + agent headers
  B->>D: Load active agent signing key
  B->>B: Verify timestamp (±300 s) and HMAC
  B->>D: Insert unique agent nonce
  B->>B: Enforce 600 events/agent/60 s
  B->>B: Pydantic schema validation
  B->>D: Store event and agent ingest audit record
  alt detection or severity >= 7
    B->>D: Create incident and link event
  end
  B-->>S: Live security_event summary
  B-->>U: 202 accepted, event ID, optional incident ID
```

The backend also applies a separate 120 requests per 60 seconds per client IP to
non-ingestion HTTP routes. Both limiters are in-memory and process-local.

## Incident investigation lifecycle

```mermaid
stateDiagram-v2
  [*] --> EventStored
  EventStored --> IncidentOpen: detection or severity >= 7
  IncidentOpen --> EvidenceLoaded: POST /api/v1/investigations
  EvidenceLoaded --> Classified: deterministic-policy
  Classified --> Persisted: evidence, severity, explanation, recommendations
  Persisted --> Audited: user investigate record
  Audited --> [*]
```

An investigation belongs to one incident. The policy loads at most 100 linked
events, sets severity to the maximum observed severity, and classifies evidence:

- `confirmed_malicious` only when structured `confirmed_indicator` is true
- `suspicious_unconfirmed` for severity 7+ or detection events
- `benign` when maximum severity is 0–2
- `insufficient_evidence` otherwise or when no events are linked

The verified investigation was ID 3 for incident 1, with event 1 as evidence,
severity 7, `suspicious_unconfirmed`, and provider `deterministic-policy`.

## Response-action approval workflow

```mermaid
sequenceDiagram
  participant R as Analyst/Admin
  participant B as Backend
  participant D as configured database
  participant A as Administrator
  R->>B: POST /api/v1/actions
  B->>B: Validate action type, target and incident
  B->>D: Store pending action + request audit
  A->>B: POST /api/v1/actions/{id}/approve
  B->>B: Require admin and pending state
  alt simulation=true
    B->>D: status=simulated, executed=true, no OS change
  else simulation=false
    B->>D: status=approved, mode=awaiting_agent
  end
  B->>D: Store approval audit and result
  B-->>A: Final status and structured result
```

The verified action was ID 1, incident 1, type `notify`, target
`security-team`, approved by user 1, and completed as a simulation. No real
notification or OS modification occurred.

## Audit logging flow

```mermaid
flowchart LR
  L[Login attempt] --> A[Audit helper]
  R[Agent registration] --> A
  E[Event ingestion] --> A
  I[Investigation] --> A
  Q[Action request] --> A
  P[Action approval] --> A
  A --> T[(audit_records)]
  T --> G[Admin GET /api/v1/audit]
```

Each audit record stores actor type/ID, action, resource type/ID, JSON details,
and a UTC creation time. There is no cryptographic append-only chain.

## Deployment architecture

```mermaid
flowchart LR
  Browser[Operator browser] -->|HTTP :5173| NG[Nginx frontend container]
  NG --> JS[React static assets]
  Browser -->|REST/WebSocket :8000| BE[FastAPI backend container]
  BE --> VOL[(agentsec-data named volume)]
  VOL --> SQ[SQLite agentsec.db]
  Agent[Windows host collector/uploader] -->|Signed HTTP :8000| BE
```

Compose builds two containers. The backend health check calls `/health`; the
frontend waits for that health check before starting. SQLite is persistent only
through the named volume and is intended for local/single-node operation.

## Trust boundaries

1. Endpoint events are untrusted even after transport authentication.
2. Agent HMAC proves possession of the signing key, not that telemetry is true.
3. Operator tokens authorize API use but are stored in browser session storage.
4. Deterministic recommendations never become executable commands.
5. Response simulation is the only verified executor.

