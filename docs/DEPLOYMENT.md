# Deployment Guide

## Database profiles

AgentSec AI selects its database at startup:

- If `DATABASE_URL` is non-empty, the backend uses PostgreSQL through Psycopg 3.
- Otherwise it uses SQLite at `AGENTSEC_DATABASE_PATH` (default `agentsec.db`).

SQLite remains the supported local-development and CI profile. Do not place a SQLite
database on an ephemeral production filesystem. PostgreSQL is the production profile.
The backend applies its idempotent versioned schema during FastAPI startup and records
version `1` in `schema_migrations`. It never copies or deletes the SQLite database.

## Local SQLite deployment

```powershell
Copy-Item .env.example .env
# Replace every example secret in .env. Leave DATABASE_URL empty.
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

The backend image sets `AGENTSEC_DATABASE_PATH=/data/agentsec.db`, and Compose mounts
the named `agentsec-data` volume at `/data`. Never run `docker compose down -v` unless
database destruction is explicitly intended.

## Supabase PostgreSQL

1. Create a Supabase project and generate a strong database password.
2. In the Supabase dashboard, open **Connect** and copy the connection URL. For a
   persistent backend with IPv6, use the direct connection. For an IPv4-only host,
   choose the shared **Session pooler**. Do not construct the pooler hostname manually.
3. Percent-encode reserved characters in the password.
4. Append `sslmode=require` (or use `sslmode=verify-full` with the downloaded Supabase
   CA certificate) and store the complete URL only in the host's secret manager.
5. Set `DATABASE_URL`; keep it out of `.env` files committed to Git and out of frontend
   variables. `AGENTSEC_DATABASE_PATH` may remain set but is ignored while
   `DATABASE_URL` is non-empty.

Supabase's official connection guidance is at
[Connect to your database](https://supabase.com/docs/guides/database/connecting-to-postgres),
and its TLS modes are described in
[Postgres SSL Enforcement](https://supabase.com/docs/guides/platform/ssl-enforcement).

### Initialize or migrate

The application performs the migration in one transaction during startup. For a new
database, deploy one backend instance first and watch its logs. Then verify:

```powershell
Invoke-RestMethod https://YOUR-BACKEND.example/health
```

Expected response:

```json
{"status":"ok","database":"ok"}
```

Initialization creates all application tables, constraints, and indexes plus the
`schema_migrations` bookkeeping table. It creates the configured bootstrap administrator
only when that username does not already exist. Startup does not reset an existing
password. Take a database backup before every future schema migration.

To validate against a dedicated, disposable PostgreSQL test database:

```powershell
$env:AGENTSEC_TEST_POSTGRES_URL = '<test database URL>'
Set-Location backend
python -m pytest tests/test_postgresql.py -q
```

Never point this integration test at a production database: it intentionally creates
agents, events, incidents, investigations, response actions, and audit records.

## Render backend deployment

1. Create a Render Web Service from the repository and select the Docker runtime.
2. Set the service root directory to `backend` and use its `Dockerfile`.
3. Configure health check path `/health`.
4. Add the environment variables below in Render's **Environment** page. Do not put
   secret values in Docker build arguments or repository files.
5. Deploy and confirm the startup logs show no migration error.
6. Call `/health`, then authenticate through `/api/v1/auth/login` over HTTPS.
7. Configure the frontend with its public backend origin and redeploy the frontend.

Render supports Docker services and pre-deploy workflows as documented in
[Docker on Render](https://render.com/docs/docker). Secret configuration is covered by
[Environment Variables and Secrets](https://render.com/docs/configure-environment-variables).

## Required production environment

| Variable | Required | Production value |
|---|---:|---|
| `AGENTSEC_ENV` | Yes | `production` |
| `DATABASE_URL` | Yes | Secret PostgreSQL URL with TLS enabled |
| `AGENTSEC_SECRET_KEY` | Yes | Unique random secret, at least 32 characters |
| `AGENTSEC_BOOTSTRAP_ADMIN` | Yes | Initial administrator username |
| `AGENTSEC_BOOTSTRAP_PASSWORD` | Yes | Unique strong initial password, at least 12 characters |
| `AGENTSEC_CORS_ORIGINS` | Yes | Comma-separated exact HTTPS frontend origins |
| `AGENTSEC_DATABASE_PATH` | No | SQLite fallback only; ignored with `DATABASE_URL` |
| `AGENTSEC_LLM_PROVIDER` | No | Existing investigation provider selection |
| `AGENTSEC_LLM_API_KEY` | Provider-dependent | Backend secret only; never a `VITE_` variable |

Generate a fresh secret and bootstrap password for every production environment. The
application rejects known development placeholders when `AGENTSEC_ENV=production`.
After the first successful login, manage and rotate credentials according to the
deployment's operational policy.

## CORS

`AGENTSEC_CORS_ORIGINS` must contain exact origins, with no path or trailing slash:

```text
https://agentsec.example.com,https://www.agentsec.example.com
```

Do not use `*` for a public security dashboard. CORS is a browser control, not an API
authorization mechanism; bearer-token RBAC and agent HMAC authentication remain
mandatory.

## Free-tier boundaries

- Supabase Free projects can be paused for low activity; review current limits and
  pausing behavior before treating one as production. See
  [Project Pausing](https://supabase.com/docs/guides/platform/free-project-pausing).
- Render Free web services currently spin down after idle periods and use an ephemeral
  local filesystem. Render explicitly advises against Free instances for production.
- Render Free PostgreSQL has storage, lifetime, backup, and pooling limitations. If
  Supabase is the database, Render also counts the connection as outbound traffic.

Current Render restrictions are maintained in
[Deploy for Free](https://render.com/docs/free). Paid, backed-up services are the
appropriate controlled-deployment baseline.

## Agent installation

Build or obtain `agentsec_collector.exe` from the same trusted source tree. Register the
agent with an administrator Bearer token, securely transfer its one-time signing key,
and run:

```powershell
python integrations\agent_uploader.py `
  --collector security-engine\agentsec_collector.exe `
  --backend https://YOUR-BACKEND.example `
  --agent-id <agent-uuid> `
  --signing-key <signing-key> `
  --once
```

Passing signing keys on command lines can expose them to local process inspection; use
an operating-system service-secret mechanism for hardened deployment.

## Production readiness checklist

1. Require HTTPS at ingress and TLS for PostgreSQL.
2. Restrict database network access and use a dedicated least-privilege database role.
3. Back up PostgreSQL and verify restoration before launch.
4. Move in-memory rate limiting to a shared store before horizontal scaling.
5. Add agent-key rotation and revocation.
6. Complete RBAC, replay, load, backup/restore, and adversarial tests.
7. Keep destructive responders disabled until a least-privilege helper and rollback
   design are reviewed and sandbox-tested.

## Troubleshooting

- Startup reports an unsupported URL: `DATABASE_URL` must begin with `postgresql://`
  or `postgres://`.
- PostgreSQL TLS failure: verify the `sslmode` and CA configuration in the URL.
- `429` on event ingestion: one agent exceeded 600 requests in 60 seconds.
- `401 expired request`: synchronize endpoint time; tolerance is five minutes.
- `409 replayed request`: generate a fresh nonce for every event.
- No incident: only `detection` or severity 7+ creates one automatically.
- No live event: WebSocket requires `?token=<operator-token>`.
