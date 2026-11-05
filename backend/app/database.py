from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .config import settings
from .security import hash_password


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('admin','analyst','viewer')), active INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS agents (
 id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, secret_hash TEXT NOT NULL,
 platform TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL,
 last_seen_at TEXT
);
CREATE TABLE IF NOT EXISTS agent_nonces (
 agent_id TEXT NOT NULL REFERENCES agents(id), nonce TEXT NOT NULL, seen_at INTEGER NOT NULL,
 PRIMARY KEY(agent_id, nonce)
);
CREATE TABLE IF NOT EXISTS security_events (
 id INTEGER PRIMARY KEY, agent_id TEXT NOT NULL REFERENCES agents(id), event_id TEXT NOT NULL,
 event_type TEXT NOT NULL, occurred_at TEXT NOT NULL, severity INTEGER NOT NULL CHECK(severity BETWEEN 0 AND 10),
 source_ip TEXT, process_id INTEGER, username TEXT, description TEXT NOT NULL,
 attributes_json TEXT NOT NULL, received_at TEXT NOT NULL,
 UNIQUE(agent_id, event_id)
);
CREATE TABLE IF NOT EXISTS threat_indicators (
 id INTEGER PRIMARY KEY, kind TEXT NOT NULL, value TEXT NOT NULL, confidence REAL NOT NULL,
 source TEXT NOT NULL, first_seen_at TEXT NOT NULL, last_seen_at TEXT NOT NULL,
 UNIQUE(kind, value, source)
);
CREATE TABLE IF NOT EXISTS incidents (
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL,
 severity INTEGER NOT NULL, category TEXT NOT NULL, summary TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS incident_events (
 incident_id INTEGER NOT NULL REFERENCES incidents(id), event_id INTEGER NOT NULL REFERENCES security_events(id),
 PRIMARY KEY(incident_id, event_id)
);
CREATE TABLE IF NOT EXISTS investigations (
 id INTEGER PRIMARY KEY, incident_id INTEGER NOT NULL REFERENCES incidents(id),
 classification TEXT NOT NULL, severity INTEGER NOT NULL, evidence_json TEXT NOT NULL,
 explanation TEXT NOT NULL, recommendations_json TEXT NOT NULL, provider TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS response_actions (
 id INTEGER PRIMARY KEY, incident_id INTEGER NOT NULL REFERENCES incidents(id), action_type TEXT NOT NULL,
 target TEXT NOT NULL, parameters_json TEXT NOT NULL, status TEXT NOT NULL, simulation INTEGER NOT NULL DEFAULT 1,
 requested_by INTEGER NOT NULL REFERENCES users(id), approved_by INTEGER REFERENCES users(id),
 requested_at TEXT NOT NULL, decided_at TEXT, executed_at TEXT, result_json TEXT
);
CREATE TABLE IF NOT EXISTS audit_records (
 id INTEGER PRIMARY KEY, actor_type TEXT NOT NULL, actor_id TEXT NOT NULL, action TEXT NOT NULL,
 resource_type TEXT NOT NULL, resource_id TEXT, details_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_events_received ON security_events(received_at DESC);
CREATE INDEX IF NOT EXISTS ix_events_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS ix_incidents_status ON incidents(status);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def initialize() -> None:
    settings.validate()
    with connection() as db:
        db.executescript(SCHEMA)
        existing = db.execute("SELECT id FROM users WHERE username=?", (settings.bootstrap_admin,)).fetchone()
        if not existing:
            db.execute(
                "INSERT INTO users(username,password_hash,role,created_at) VALUES(?,?,?,?)",
                (settings.bootstrap_admin, hash_password(settings.bootstrap_password), "admin", utc_now()),
            )

