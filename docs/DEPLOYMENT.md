# Deployment Guide

## Supported verified profile

- Windows 11 host
- Docker Desktop and Docker Compose
- FastAPI backend container
- Nginx/React frontend container
- SQLite database in `agentsec-data`
- Native Windows collector and Python uploader on the monitored endpoint

## Local deployment

```powershell
Copy-Item .env.example .env
# Replace all example secrets in .env.
docker compose config
docker compose up --build -d
docker compose ps
```

Verify:

```powershell
Invoke-RestMethod http://localhost:8000/health
(Invoke-WebRequest http://localhost:5173).StatusCode
```

Expected values are `{status: ok, database: ok}` and HTTP 200. Swagger is at
`http://localhost:8000/docs`.

## Persistence

The backend image sets `AGENTSEC_DATABASE_PATH=/data/agentsec.db`. Compose mounts
the named `agentsec-data` volume at `/data`. Do not use `docker compose down -v`
unless database destruction is explicitly intended. Restart persistence has not
been independently verified and should be tested before relying on the volume.

## Agent installation

Build or obtain `agentsec_collector.exe` from the same trusted source tree. Run
it as an ordinary user first; administrator rights are not documented as a
requirement for the implemented APIs.

Register the agent with an administrator Bearer token, securely transfer the
one-time signing key, and run:

```powershell
python integrations\agent_uploader.py `
  --collector security-engine\agentsec_collector.exe `
  --backend http://localhost:8000 `
  --agent-id <agent-uuid> `
  --signing-key <signing-key> `
  --once
```

For remote deployment, replace HTTP with HTTPS. Passing signing keys on command
lines can expose them to local process inspection; a service-secret mechanism is
required for hardened deployment.

## Production readiness boundaries

This Compose profile is appropriate for controlled local demonstration. Before
Internet or multi-node deployment:

1. Add TLS and restrictive ingress.
2. Replace SQLite with a supported production database and migrations.
3. Move rate limiting to a shared store.
4. Add agent-key rotation and revocation.
5. Add secrets management rather than `.env` distribution.
6. Complete RBAC, replay, load and adversarial tests.
7. Add backups and verify restore/restart persistence.
8. Keep destructive responders disabled until a least-privilege helper and
   rollback design are reviewed and sandbox-tested.

## Troubleshooting

- `429` on event ingestion: one agent exceeded 600 requests in 60 seconds.
- `401 expired request`: synchronize endpoint time; tolerance is five minutes.
- `409 replayed request`: generate a fresh nonce for every event.
- No incident: only `detection` or severity 7+ creates one automatically.
- No live event: WebSocket requires `?token=<operator-token>`.

