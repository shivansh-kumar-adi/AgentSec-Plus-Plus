import pytest

from app.config import settings
from app.database import connection, initialize


@pytest.mark.skipif(bool(settings.database_url), reason="SQLite schema assertion")
def test_sqlite_schema_contains_all_application_tables():
    initialize()
    with connection() as db:
        rows = db.execute(
            "SELECT name FROM sqlite_master WHERE type=? AND name NOT LIKE ?",
            ("table", "sqlite_%"),
        ).fetchall()
    names = {row["name"] for row in rows}
    assert {
        "users",
        "agents",
        "agent_nonces",
        "security_events",
        "threat_indicators",
        "incidents",
        "incident_events",
        "investigations",
        "response_actions",
        "audit_records",
        "schema_migrations",
    } <= names
