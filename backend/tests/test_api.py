import hashlib
import hmac
import json
import os
import time
import uuid

os.environ.setdefault("AGENTSEC_DATABASE_PATH", "test-agentsec.db")
os.environ["AGENTSEC_SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes"
os.environ["AGENTSEC_BOOTSTRAP_PASSWORD"] = "correct-horse-battery-staple"

from fastapi.testclient import TestClient

try:
    from app.main import app
except ModuleNotFoundError:
    from backend.app.main import app


def test_health_auth_ingestion_and_investigation(tmp_path):
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"

        login = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "correct-horse-battery-staple",
            },
        )
        assert login.status_code == 200

        headers = {
            "Authorization": f"Bearer {login.json()['access_token']}"
        }

        created = client.post(
            "/api/v1/agents",
            headers=headers,
            json={
                "name": f"test-{uuid.uuid4().hex[:8]}",
                "platform": "windows",
            },
        )
        assert created.status_code == 201

        agent = created.json()

        payload = {
            "event_id": uuid.uuid4().hex,
            "event_type": "detection",
            "occurred_at": "2026-11-05T10:00:00Z",
            "severity": 8,
            "source_ip": "203.0.113.10",
            "description": "Controlled integration test",
            "attributes": {"confirmed_indicator": False},
        }

        body = json.dumps(payload, separators=(",", ":")).encode()
        timestamp = str(int(time.time()))
        nonce = uuid.uuid4().hex

        message = (
            f"{timestamp}\n{nonce}\n{hashlib.sha256(body).hexdigest()}"
        ).encode()

        signature = hmac.new(
            bytes.fromhex(agent["signing_key"]),
            message,
            hashlib.sha256,
        ).hexdigest()

        ingest_headers = {
            "X-Agent-Id": agent["id"],
            "X-Agent-Timestamp": timestamp,
            "X-Agent-Nonce": nonce,
            "X-Agent-Signature": signature,
            "Content-Type": "application/json",
        }

        response = client.post(
            "/api/v1/events",
            headers=ingest_headers,
            content=body,
        )
        assert response.status_code == 202

        replay = client.post(
            "/api/v1/events",
            headers=ingest_headers,
            content=body,
        )
        assert replay.status_code == 409

        duplicate_nonce = uuid.uuid4().hex

        duplicate_message = (
            f"{timestamp}\n{duplicate_nonce}\n"
            f"{hashlib.sha256(body).hexdigest()}"
        ).encode()

        duplicate_headers = {
            **ingest_headers,
            "X-Agent-Nonce": duplicate_nonce,
            "X-Agent-Signature": hmac.new(
                bytes.fromhex(agent["signing_key"]),
                duplicate_message,
                hashlib.sha256,
            ).hexdigest(),
        }

        duplicate = client.post(
            "/api/v1/events",
            headers=duplicate_headers,
            content=body,
        )
        assert duplicate.status_code == 409

        incident_id = response.json()["incident_id"]
        assert incident_id

        events = client.get("/api/v1/events", headers=headers)
        assert events.status_code == 200
        assert any(
            item["event_id"] == payload["event_id"]
            for item in events.json()
        )

        incidents = client.get("/api/v1/incidents", headers=headers)
        assert incidents.status_code == 200
        assert any(
            item["id"] == incident_id
            for item in incidents.json()
        )

        investigation = client.post(
            "/api/v1/investigations",
            headers=headers,
            json={"incident_id": incident_id},
        )
        assert investigation.status_code == 201
        assert (
            investigation.json()["classification"]
            == "suspicious_unconfirmed"
        )

        # Verify simulated response action workflow.
        action = client.post(
            "/api/v1/actions",
            headers=headers,
            json={
                "incident_id": incident_id,
                "action_type": "notify",
                "target": "integration-test",
                "parameters": {},
                "simulation": True,
            },
        )
        assert action.status_code == 201

        approval = client.post(
            f"/api/v1/actions/{action.json()['id']}/approve",
            headers=headers,
        )
        assert approval.status_code == 200
        assert approval.json()["status"] == "simulated"
        assert approval.json()["result"]["executed"] is True

        # Verify audit records.
        audit = client.get("/api/v1/audit", headers=headers)
        assert audit.status_code == 200

        actions = {
            record["action"]
            for record in audit.json()
        }

        assert {
            "create",
            "ingest",
            "investigate",
            "request",
            "approve",
        } <= actions