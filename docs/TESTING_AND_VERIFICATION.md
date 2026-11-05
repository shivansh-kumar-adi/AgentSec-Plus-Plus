# Testing and Verification Report

Report date: 2026-11-05. Status meanings: **PASS** means the check was actually
observed; **PARTIAL** means only part of the behavior was exercised; **NOT
TESTED** means no successful execution evidence is available.

## Deployment checks

| Check | Status | Evidence |
|---|---|---|
| Docker Compose configuration validation | PASS | `docker compose config` completed successfully in the supplied runtime verification. |
| Backend container startup | PASS | Backend reached healthy state. |
| Frontend container startup | PASS | Frontend container ran and served content. |
| Backend health | PASS | `/health` returned `status=ok`, `database=ok`. |
| Frontend HTTP | PASS | `http://localhost:5173` returned HTTP 200. |
| Swagger UI | PASS | `/docs` loaded successfully. |
| SQLite container persistence | PARTIAL | Named volume is configured and records persisted during the running deployment; persistence across a deliberate container restart was not separately verified. |

## Agent integration checks

| Check | Status | Evidence |
|---|---|---|
| Windows collector execution | PASS | Native collector executed successfully. |
| Process collection | PASS | Collector produced real process JSONL during earlier verification. |
| Network connection collection | PASS | Verified run produced `network_connection` events. |
| Python uploader | PASS | Signed collector events were accepted by the backend. |
| HMAC authentication | PASS | Uploader-generated HMAC requests were accepted. |
| Per-agent event limiting | PASS | Earlier HTTP 429 behavior was addressed by the implemented 600 events/agent/60 s limiter; non-event routes remain separately IP-limited. |
| Backend event retrieval | PASS | Persisted events were returned, including IDs 725–734. |
| Automatic incident from newly collected network events | NOT TESTED | No verification evidence that those low-severity network events created an incident. |

## Investigation checks

| Check | Status | Evidence |
|---|---|---|
| Incident listing | PASS | Incident ID 1 returned with severity 7. |
| Investigation creation | PASS | Investigation ID 3 created for incident 1. |
| Evidence linkage | PASS | Evidence referenced security event ID 1. |
| Classification | PASS | `suspicious_unconfirmed`. |
| Severity calculation | PASS | Maximum linked severity returned as 7. |
| Provider identity | PASS | `deterministic-policy`. |
| LLM investigation | NOT TESTED | No LLM call exists in the current implementation. |

Verified explanation:

> Policy classified 1 related event(s); maximum observed severity is 7.

## Response-action checks

| Check | Status | Evidence |
|---|---|---|
| Create simulated notification | PASS | Action ID 1, incident 1, `notify`, target `security-team`. |
| Pending state | PASS | Initial request returned pending. |
| Admin approval | PASS | Approval accepted for authenticated user ID 1. |
| Final simulation state | PASS | Final status became `simulated`. |
| OS modification | NOT TESTED | Intentionally not performed. |
| Real notification delivery | NOT TESTED | Simulation did not send a notification. |

Verified result:

```json
{
  "executed": true,
  "mode": "simulation",
  "message": "No operating-system change was made."
}
```

## Audit checks

| Audit ID | Actor | Action | Resource | Status |
|---:|---|---|---|---|
| 743 | user | approve | response_action 1 | PASS |
| 742 | user | request | response_action 1 | PASS |
| 741 | user | investigate | incident 1 | PASS |
| 740–736 | agent | ingest | security events 734–730 | PASS |

## Security and negative testing

| Check | Status | Notes |
|---|---|---|
| Invalid password | PARTIAL | Covered by source/tests, but not part of the supplied container verification. |
| Nonce replay rejection | NOT TESTED | Database uniqueness is implemented; a dedicated runtime negative test remains. |
| Expired timestamp | NOT TESTED | ±300-second validation exists but was not separately exercised. |
| RBAC matrix | PARTIAL | Admin path verified; analyst/viewer denial boundaries require dedicated tests. |
| Adversarial input/prompt injection | NOT TESTED | Deterministic policy does not execute text, but adversarial testing remains. |
| Production load | NOT TESTED | No sustained or multi-worker load test was run. |

## Component build/test evidence

| Component | Status | Result |
|---|---|---|
| Legacy C++ tests | PASS | 6/6 assertion tests reran successfully during final packaging. |
| Backend pytest | PARTIAL | Test collection succeeded, but the single integration test did not complete in two attempts and was interrupted after producing no result. The earlier engineering record contains a passing run; this packaging run is not counted as a pass. |
| Frontend production build | PASS | Current TypeScript/Vite build rerun during final packaging; warnings, if any, are recorded in the final validation summary. |
| Compose schema/interpolation | PASS | Current configuration validation rerun during final packaging. |
| Live container query from packaging sandbox | PARTIAL | Runtime was verified by the user; the packaging sandbox could not access Docker's named pipe. |

## Final packaging validation

| Validation | Status | Result |
|---|---|---|
| FastAPI OpenAPI generation | PASS | Generated route map matched documented HTTP routes. |
| Frontend build/type check | PASS | 2,428 modules transformed; output completed with a non-fatal bundle-size warning. |
| Compose configuration | PASS | `docker compose config --quiet` completed successfully. |
| C++ tests | PASS | 6/6 passed. |
| Backend pytest | PARTIAL | One test collected but did not complete in two attempts; no pass was claimed. |
| ZIP exclusion scan | PASS | No `.env`, database, executable, object, cache, dependency, build, log, JSONL or backup artifacts found. |
| ZIP secret-pattern scan | PASS | No private keys, cloud-key patterns, Bearer tokens or non-placeholder embedded credentials found. |
| ZIP required-file inspection | PASS | README, documentation, backend, frontend, collector, uploader and Compose sources present. |

## Final deployment verification

- Backend container: **PASS — healthy**
- Frontend container: **PASS — running**
- Frontend HTTP response: **PASS — 200**
- Backend/database health: **PASS — previously verified**
- Container restart persistence: **NOT TESTED**

## Remaining verification gaps

- Dedicated nonce-replay and stale-timestamp negative tests
- Full RBAC role/route matrix
- Container restart persistence
- Production load, concurrency and multi-worker rate-limit behavior
- Adversarial security review and fuzzing
- Broader Windows telemetry coverage
- Real response adapters (deliberately absent)

