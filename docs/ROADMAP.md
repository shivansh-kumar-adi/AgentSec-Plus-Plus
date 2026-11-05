# Roadmap and Feature Completion Matrix

## Current completion matrix

| Capability | Status | Verification / boundary |
|---|---|---|
| React dashboard | Implemented, tested | Production build and HTTP 200 verified |
| FastAPI health/auth | Implemented, tested | Health and admin login verified |
| RBAC route gates | Implemented, partially tested | Admin workflow verified; complete matrix pending |
| Agent registration | Implemented, tested | Signed uploader workflow used registered agent |
| Windows process collection | Implemented, tested | Real process events observed |
| Windows TCP collection | Implemented, tested | `network_connection` events observed |
| Authentication/file telemetry | Schema-supported, unverified | No verified collector implementation |
| Signed event ingestion | Implemented, tested | HMAC uploader events persisted |
| Timestamp/nonce replay protection | Implemented, unverified negatively | Dedicated replay test pending |
| Per-agent rate limiting | Implemented, tested operationally | 600 events/60 s; earlier 429 issue addressed |
| SQLite persistence | Implemented, API flow tested | Restart persistence pending |
| PostgreSQL persistence | Implemented, unverified against a live server | Run `tests/test_postgresql.py` with a dedicated test database |
| Incident creation | Implemented, partially tested | Incident 1 verified; new network-event generation unverified |
| Deterministic investigation | Implemented, tested | Investigation 3, incident 1, event 1 |
| LLM investigation | Not implemented | Configuration fields only |
| Response requests/approval | Implemented, tested | Simulated notification action 1 |
| Real response execution | Not implemented | Deliberately stops at awaiting-agent |
| Audit logging | Implemented, tested | IDs 736–743 verified |
| WebSocket streaming | Implemented, unverified | Dedicated client test pending |
| Docker deployment | Implemented, tested | Containers/health/frontend verified |
| PostgreSQL/migrations | Implemented, not live-server verified | Versioned startup schema supports SQLite and PostgreSQL |
| Linux collector | Not implemented | No Linux source in current tree |

## Near-term engineering priorities

1. Add negative tests for replay, stale timestamp, invalid HMAC and duplicate ID.
2. Verify all RBAC role/route combinations.
3. Verify Docker restart persistence and backup/restore.
4. Add incident detail and investigation listing endpoints if product needs them.
5. Improve Windows collector health reporting and broaden telemetry.
6. Add shared/distributed rate limiting before multi-worker deployment.

## Future research and production work

- Constrained LLM enrichment with JSON-schema validation, prompt-injection
  isolation, evidence citations and deterministic policy override
- PostgreSQL with versioned migrations
- Linux `/proc`, socket and authentication collectors
- Least-privilege response helper with target validation, TTL and rollback
- SIEM/threat-intelligence integrations
- Cryptographically anchored audit export
- Load, soak, fuzz and adversarial testing

