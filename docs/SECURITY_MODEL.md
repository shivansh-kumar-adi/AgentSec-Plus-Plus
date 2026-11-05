# Security Model

## Assets

- Operator credentials and access tokens
- Agent enrollment material and signing keys
- Endpoint telemetry and incident evidence
- SQLite database and Docker volume
- Response approval and audit history

## Identities and authorization

Operator passwords use PBKDF2-HMAC-SHA256 with a random 16-byte salt and
310,000 iterations. Successful login returns a server-secret HMAC-signed token
with user ID, role, expiry, and nonce. Tokens expire after one hour.

Roles:

| Role | Effective access in current routes |
|---|---|
| viewer | Read events, incidents and actions |
| analyst | Viewer access plus create investigations and simulated actions |
| admin | All implemented operator routes, agent registration, approvals and audit |

The full denial matrix has not been independently verified.

## Agent trust and request signing

Agent registration is admin-only. The backend generates random enrollment
material, derives a keyed digest using the server secret, stores it, and returns
the corresponding hexadecimal signing key once.

Every event request includes agent ID, Unix timestamp, nonce and signature. The
signature covers the exact body SHA-256 hash:

```text
HMAC-SHA256(signing_key, timestamp + LF + nonce + LF + body_sha256)
```

The backend uses constant-time signature comparison, accepts timestamps within
five minutes, requires a nonce of at least 16 characters, and inserts each nonce
under a unique `(agent_id, nonce)` database key. Nonces older than ten minutes
are pruned. A dedicated negative replay test remains pending.

## Rate limiting

- Non-event HTTP routes: 120 requests/client IP/60 seconds
- Event ingestion: 600 requests/verified agent/60 seconds

Both buckets are in-memory and process-local. They are not shared across Uvicorn
workers or replicas and reset on process restart.

## Input validation

Pydantic bounds event identifiers, types, severity, text lengths, process IDs,
and attribute size, and rejects unknown event properties. SQL uses positional
parameters. Event text remains untrusted after validation.

## Investigation safety

The provider is deterministic policy code. It reads structured database fields,
does not call an LLM, does not interpret log text as instructions, and does not
execute commands. `confirmed_malicious` requires the structured
`confirmed_indicator=true` attribute.

## Response safety

Action types are an enum. Targets and parameters are stored as data. Requests
start pending and approvals require an administrator. Verified simulation only
records a structured result. For `simulation=false`, approval stops at
`awaiting_agent`; there is no privileged executor or arbitrary-command path.

## Audit model

Login, registration, ingestion, investigation, request and approval operations
write audit rows. Records are database entries, not cryptographically chained or
write-once storage. Database administrators can modify them.

## Browser and transport considerations

The frontend stores its token in session storage. CORS is allow-listed from the
environment. The local deployment uses HTTP; production must add HTTPS, secure
proxy headers, restrictive network policy, and preferably HttpOnly same-site
session cookies through a backend-for-frontend design.

## Known security gaps

- No TLS termination in Compose
- SQLite file and named-volume access rely on host/Docker controls
- No distributed rate-limit store
- No token revocation list or refresh-token flow
- No agent-key rotation/revocation endpoint
- No cryptographic audit chain
- Incomplete RBAC and adversarial testing
- No privileged response helper or rollback implementation

