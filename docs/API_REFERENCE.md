# API Reference

Source of truth: `backend/app/main.py`, `backend/app/schemas.py`, and locally
generated FastAPI OpenAPI. Base URL in the local Compose deployment is
`http://localhost:8000`.

## Registered routes

| Method | Endpoint | Authorization | Purpose |
|---|---|---|---|
| GET | `/health` | None | Backend/database health |
| POST | `/api/v1/auth/login` | None | Authenticate operator |
| POST | `/api/v1/agents` | Admin Bearer token | Register agent |
| POST | `/api/v1/events` | Signed agent headers | Ingest one event |
| GET | `/api/v1/events` | Admin/analyst/viewer | Retrieve events |
| GET | `/api/v1/incidents` | Admin/analyst/viewer | List incidents |
| POST | `/api/v1/investigations` | Admin/analyst | Create investigation |
| POST | `/api/v1/actions` | Admin/analyst | Request action |
| GET | `/api/v1/actions` | Admin/analyst/viewer | List actions |
| POST | `/api/v1/actions/{action_id}/approve` | Admin | Approve pending action |
| GET | `/api/v1/audit` | Admin | List audit records |
| WS | `/ws/events?token=<token>` | Signed operator token | Receive event summaries |

Not registered: `GET /api/v1/agents`, `GET /api/v1/incidents/{id}`, and any
GET/list route for investigations.

## Authentication

### `POST /api/v1/auth/login`

```json
{"username":"admin","password":"<configured-password>"}
```

Successful response contains `access_token`, `token_type`, and user `id`,
`username`, and `role`. Protected operator routes require:

```http
Authorization: Bearer <access_token>
```

## Agent registration

### `POST /api/v1/agents`

```json
{"name":"windows-lab","platform":"windows"}
```

- `name`: 1–64 characters matching `[A-Za-z0-9_.-]`
- `platform`: `windows` or `linux`

HTTP 201 returns UUID, name, platform, one-time `secret`, `signing_key`, and a
storage warning. The implemented uploader uses `signing_key`.

## Event ingestion

### `POST /api/v1/events`

Headers:

```http
Content-Type: application/json
X-Agent-Id: <agent UUID>
X-Agent-Timestamp: <Unix seconds>
X-Agent-Nonce: <at least 16 characters>
X-Agent-Signature: <lowercase hexadecimal HMAC-SHA256>
```

Schema:

```json
{
  "event_id": "unique-event-id",
  "event_type": "process",
  "occurred_at": "2026-11-05T10:00:00Z",
  "severity": 1,
  "source_ip": "127.0.0.1",
  "process_id": 1234,
  "username": "optional-user",
  "description": "Process observed",
  "attributes": {"image":"example.exe"}
}
```

Required fields are `event_id` (8–128), `event_type`, `occurred_at`, `severity`
(0–10), and `description` (1–1024). Event type must be `process`,
`network_connection`, `authentication`, `file_change`, or `detection`. Unknown
fields are forbidden; attributes are limited to 50 keys and roughly 16 KiB.

Signature input:

```text
body_hash = hex(SHA256(exact request body bytes))
message = timestamp + "\n" + nonce + "\n" + body_hash
signature = hex(HMAC-SHA256(bytes.fromhex(signing_key), UTF8(message)))
```

Timestamp tolerance is ±300 seconds. Agent/nonce uniqueness provides replay
rejection; nonces older than 600 seconds are removed. A successful response is:

```json
{"accepted":true,"id":734,"incident_id":null}
```

`incident_id` is populated for detection events or severity 7+ events.

## Events and incidents

### `GET /api/v1/events`

Optional query parameters:

- `limit`: clamped to 1–500, default 100
- `event_type`: exact database filter

Returns newest events first, including parsed `attributes` and stored
`attributes_json`.

### `GET /api/v1/incidents`

Returns at most 500 incidents ordered by `updated_at` descending.

## Investigations

### `POST /api/v1/investigations`

```json
{"incident_id":1}
```

HTTP 201 returns investigation ID, incident ID, classification, severity,
evidence array, explanation, recommendations, and provider. There is no GET
investigation route.

## Response actions

### `POST /api/v1/actions`

```json
{
  "incident_id":1,
  "action_type":"notify",
  "target":"security-team",
  "parameters":{},
  "simulation":true
}
```

Supported types: `block_ip`, `terminate_process`, `quarantine_file`,
`disable_account`, and `notify`. Target length is 1–512. Non-admin users cannot
request `simulation=false`. A valid request returns `pending`.

### `POST /api/v1/actions/{action_id}/approve`

Admin only. Pending simulated actions become `simulated` and return:

```json
{
  "id":1,
  "status":"simulated",
  "result":{"executed":true,"mode":"simulation","message":"No operating-system change was made."}
}
```

Non-simulation actions become `approved` with mode `awaiting_agent`; there is no
privileged executor in this codebase.

## Audit and live stream

`GET /api/v1/audit` returns up to 500 newest records and is admin-only.
`/ws/events` requires a token query parameter and sends event summary objects
after ingestion.

## Error behavior

| Status | Meaning |
|---|---|
| 401 | Missing/invalid operator token, unknown agent, invalid signature, or stale timestamp |
| 403 | RBAC role does not authorize operation |
| 404 | Incident/action not found |
| 409 | Duplicate agent name, replayed nonce, duplicate event, or non-pending action |
| 422 | Pydantic/request validation failure |
| 429 | Client or per-agent rate limit exceeded |

