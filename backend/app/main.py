from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import connection, initialize, utc_now
from .investigation import investigate
from .schemas import ActionRequest, AgentCreate, InvestigationRequest, LoginRequest, SecurityEventIn
from .security import (create_access_token, decode_access_token, hash_agent_secret,
                       new_agent_secret, verify_password)


RATE_WINDOW_SECONDS = 60
RATE_LIMIT = 120
AGENT_EVENT_RATE_LIMIT = 600

rate_buckets: dict[str, deque[float]] = defaultdict(deque)
agent_event_rate_buckets: dict[str, deque[float]] = defaultdict(deque)
websocket_clients: set[WebSocket] = set()


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize()
    yield


app = FastAPI(title="AgentSec AI API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=False,
                   allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type",
                   "X-Agent-Id", "X-Agent-Timestamp", "X-Agent-Nonce", "X-Agent-Signature"])


@app.middleware("http")
async def security_headers_and_rate_limit(request: Request, call_next):
    # Agent events use a separate per-agent limit after signature verification.
    if request.url.path != "/api/v1/events":
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        bucket = rate_buckets[key]

        while bucket and bucket[0] < now - RATE_WINDOW_SECONDS:
            bucket.popleft()

        if len(bucket) >= RATE_LIMIT:
            return __import__("fastapi").responses.JSONResponse(
                {"detail": "rate limit exceeded"},
                status_code=429
            )

        bucket.append(now)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


def current_user(authorization: str = Header(default="")) -> dict[str, Any]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    payload = decode_access_token(authorization[7:])
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired token")
    with connection() as db:
        user = db.execute("SELECT id,username,role,active FROM users WHERE id=?", (payload["sub"],)).fetchone()
    if not user or not user["active"]:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "inactive user")
    return dict(user)


def require_role(*roles: str):
    def dependency(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        if user["role"] not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "insufficient role")
        return user
    return dependency


def audit(db, actor_type: str, actor_id: str, action: str, resource_type: str,
          resource_id: str | None = None, details: dict[str, Any] | None = None) -> None:
    db.execute("INSERT INTO audit_records(actor_type,actor_id,action,resource_type,resource_id,details_json,created_at) "
               "VALUES(?,?,?,?,?,?,?)", (actor_type, actor_id, action, resource_type, resource_id,
               json.dumps(details or {}, separators=(",", ":")), utc_now()))


def verify_agent_request(request: Request, body: bytes, agent_id: str, timestamp_text: str,
                         nonce: str, supplied: str) -> None:
    try:
        timestamp_value = int(timestamp_text)
    except ValueError as exc:
        raise HTTPException(401, "invalid agent timestamp") from exc
    if abs(int(time.time()) - timestamp_value) > 300 or len(nonce) < 16:
        raise HTTPException(401, "expired request or invalid nonce")
    with connection() as db:
        agent = db.execute("SELECT secret_hash,active FROM agents WHERE id=?", (agent_id,)).fetchone()
        if not agent or not agent["active"]:
            raise HTTPException(401, "unknown agent")
        body_hash = hashlib.sha256(body).hexdigest()
        message = f"{timestamp_text}\n{nonce}\n{body_hash}".encode()
        expected = hmac.new(bytes.fromhex(agent["secret_hash"]), message, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, supplied):
            raise HTTPException(401, "invalid agent signature")
        try:
            db.execute("INSERT INTO agent_nonces(agent_id,nonce,seen_at) VALUES(?,?,?)",
                       (agent_id, nonce, timestamp_value))
        except Exception as exc:
            raise HTTPException(409, "replayed request") from exc
        db.execute("DELETE FROM agent_nonces WHERE seen_at<?", (int(time.time()) - 600,))


def enforce_agent_event_rate_limit(agent_id: str) -> None:
    now = time.monotonic()
    bucket = agent_event_rate_buckets[agent_id]

    while bucket and bucket[0] < now - RATE_WINDOW_SECONDS:
        bucket.popleft()

    if len(bucket) >= AGENT_EVENT_RATE_LIMIT:
        raise HTTPException(429, "agent event rate limit exceeded")

    bucket.append(now)


@app.get("/health")
def health() -> dict[str, str]:
    with connection() as db:
        db.execute("SELECT 1").fetchone()
    return {"status": "ok", "database": "ok"}


@app.post("/api/v1/auth/login")
def login(payload: LoginRequest) -> dict[str, Any]:
    with connection() as db:
        user = db.execute("SELECT * FROM users WHERE username=?", (payload.username,)).fetchone()
        if not user or not user["active"] or not verify_password(payload.password, user["password_hash"]):
            audit(db, "anonymous", payload.username[:64], "login_failed", "session")
            raise HTTPException(401, "invalid credentials")
        audit(db, "user", str(user["id"]), "login", "session")
        return {"access_token": create_access_token(user["id"], user["role"]), "token_type": "bearer",
                "user": {"id": user["id"], "username": user["username"], "role": user["role"]}}


@app.post("/api/v1/agents", status_code=201)
def create_agent(payload: AgentCreate, user=Depends(require_role("admin"))) -> dict[str, Any]:
    agent_id, secret = str(uuid.uuid4()), new_agent_secret()
    # Store a keyed digest as the HMAC key; the raw enrollment secret is returned once.
    stored_key = hash_agent_secret(secret)
    with connection() as db:
        try:
            db.execute("INSERT INTO agents(id,name,secret_hash,platform,created_at) VALUES(?,?,?,?,?)",
                       (agent_id, payload.name, stored_key, payload.platform, utc_now()))
        except Exception as exc:
            raise HTTPException(409, "agent name already exists") from exc
        audit(db, "user", str(user["id"]), "create", "agent", agent_id, {"name": payload.name})
    return {"id": agent_id, "name": payload.name, "platform": payload.platform,
            "secret": secret, "signing_key": stored_key,
            "warning": "Store the enrollment material securely; it is shown only once."}


@app.post("/api/v1/events", status_code=202)
async def ingest_event(request: Request, x_agent_id: str = Header(), x_agent_timestamp: str = Header(),
                       x_agent_nonce: str = Header(), x_agent_signature: str = Header()) -> dict[str, Any]:
    body = await request.body()
    verify_agent_request(request, body, x_agent_id, x_agent_timestamp, x_agent_nonce, x_agent_signature)
    enforce_agent_event_rate_limit(x_agent_id)
    try:
        event = SecurityEventIn.model_validate_json(body)
    except Exception as exc:
        raise HTTPException(422, "invalid event payload") from exc
    now = utc_now()
    with connection() as db:
        try:
            event_db_id = db.insert_id(
                "INSERT INTO security_events(agent_id,event_id,event_type,occurred_at,severity,source_ip,process_id,username,description,attributes_json,received_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (x_agent_id, event.event_id, event.event_type, event.occurred_at.isoformat(), event.severity,
                 event.source_ip, event.process_id, event.username, event.description,
                 json.dumps(event.attributes, separators=(",", ":")), now),
            )
        except Exception as exc:
            raise HTTPException(409, "duplicate event") from exc
        incident_id = None
        if event.severity >= 7 or event.event_type == "detection":
            title = f"{event.event_type.replace('_', ' ').title()} on agent {x_agent_id[:8]}"
            incident_id = db.insert_id("INSERT INTO incidents(title,status,severity,category,summary,created_at,updated_at) "
                                       "VALUES(?,?,?,?,?,?,?)", (title, "open", event.severity, event.event_type,
                                       event.description, now, now))
            db.execute("INSERT INTO incident_events(incident_id,event_id) VALUES(?,?)", (incident_id, event_db_id))
        db.execute("UPDATE agents SET last_seen_at=? WHERE id=?", (now, x_agent_id))
        audit(db, "agent", x_agent_id, "ingest", "security_event", str(event_db_id),
              {"event_type": event.event_type, "incident_id": incident_id})
    message = {"type": "security_event", "id": event_db_id, "severity": event.severity,
               "event_type": event.event_type, "incident_id": incident_id, "received_at": now}
    for client in list(websocket_clients):
        try:
            await client.send_json(message)
        except Exception:
            websocket_clients.discard(client)
    return {"accepted": True, "id": event_db_id, "incident_id": incident_id}


@app.get("/api/v1/events")
def list_events(limit: int = 100, event_type: str | None = None,
                user=Depends(require_role("admin", "analyst", "viewer"))) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 500))
    with connection() as db:
        if event_type:
            rows = db.execute("SELECT * FROM security_events WHERE event_type=? ORDER BY id DESC LIMIT ?",
                              (event_type, limit)).fetchall()
        else:
            rows = db.execute("SELECT * FROM security_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{**dict(row), "attributes": json.loads(row["attributes_json"])} for row in rows]


@app.get("/api/v1/incidents")
def list_incidents(user=Depends(require_role("admin", "analyst", "viewer"))) -> list[dict[str, Any]]:
    with connection() as db:
        rows = db.execute("SELECT * FROM incidents ORDER BY updated_at DESC LIMIT 500").fetchall()
    return [dict(row) for row in rows]


@app.post("/api/v1/investigations", status_code=201)
def create_investigation(payload: InvestigationRequest,
                         user=Depends(require_role("admin", "analyst"))) -> dict[str, Any]:
    with connection() as db:
        incident = db.execute("SELECT * FROM incidents WHERE id=?", (payload.incident_id,)).fetchone()
        if not incident:
            raise HTTPException(404, "incident not found")
        rows = db.execute("SELECT e.* FROM security_events e JOIN incident_events ie ON ie.event_id=e.id "
                          "WHERE ie.incident_id=? ORDER BY e.occurred_at DESC LIMIT 100",
                          (payload.incident_id,)).fetchall()
        result = investigate([dict(row) for row in rows])
        investigation_id = db.insert_id("INSERT INTO investigations(incident_id,classification,severity,evidence_json,explanation,recommendations_json,provider,created_at) "
                                         "VALUES(?,?,?,?,?,?,?,?)", (payload.incident_id, result["classification"],
                                         result["severity"], json.dumps(result["evidence"]), result["explanation"],
                                         json.dumps(result["recommendations"]), result["provider"], utc_now()))
        audit(db, "user", str(user["id"]), "investigate", "incident", str(payload.incident_id),
              {"investigation_id": investigation_id})
    return {"id": investigation_id, "incident_id": payload.incident_id, **result}


@app.post("/api/v1/actions", status_code=201)
def request_action(payload: ActionRequest, user=Depends(require_role("admin", "analyst"))) -> dict[str, Any]:
    if not payload.simulation and user["role"] != "admin":
        raise HTTPException(403, "only administrators may request real actions")
    now = utc_now()
    with connection() as db:
        if not db.execute("SELECT id FROM incidents WHERE id=?", (payload.incident_id,)).fetchone():
            raise HTTPException(404, "incident not found")
        action_id = db.insert_id("INSERT INTO response_actions(incident_id,action_type,target,parameters_json,status,simulation,requested_by,requested_at) "
                                 "VALUES(?,?,?,?,?,?,?,?)", (payload.incident_id, payload.action_type, payload.target,
                                 json.dumps(payload.parameters), "pending", int(payload.simulation), user["id"], now))
        audit(db, "user", str(user["id"]), "request", "response_action", str(action_id),
              {"simulation": payload.simulation})
    return {"id": action_id, "status": "pending", "simulation": payload.simulation}


@app.post("/api/v1/actions/{action_id}/approve")
def approve_action(action_id: int, user=Depends(require_role("admin"))) -> dict[str, Any]:
    now = utc_now()
    with connection() as db:
        action = db.execute("SELECT * FROM response_actions WHERE id=?", (action_id,)).fetchone()
        if not action:
            raise HTTPException(404, "action not found")
        if action["status"] != "pending":
            raise HTTPException(409, "action is not pending")
        # Deliberately execute simulation only. Real adapters require a separate least-privilege helper.
        status_value = "simulated" if action["simulation"] else "approved"
        result = {"executed": bool(action["simulation"]), "mode": "simulation" if action["simulation"] else "awaiting_agent",
                  "message": "No operating-system change was made."}
        db.execute("UPDATE response_actions SET status=?,approved_by=?,decided_at=?,executed_at=?,result_json=? WHERE id=?",
                   (status_value, user["id"], now, now if action["simulation"] else None,
                    json.dumps(result), action_id))
        audit(db, "user", str(user["id"]), "approve", "response_action", str(action_id), result)
    return {"id": action_id, "status": status_value, "result": result}


@app.get("/api/v1/actions")
def list_actions(user=Depends(require_role("admin", "analyst", "viewer"))) -> list[dict[str, Any]]:
    with connection() as db:
        rows = db.execute("SELECT * FROM response_actions ORDER BY id DESC LIMIT 500").fetchall()
    return [dict(row) for row in rows]


@app.get("/api/v1/audit")
def list_audit(user=Depends(require_role("admin"))) -> list[dict[str, Any]]:
    with connection() as db:
        rows = db.execute("SELECT * FROM audit_records ORDER BY id DESC LIMIT 500").fetchall()
    return [dict(row) for row in rows]


@app.websocket("/ws/events")
async def event_stream(websocket: WebSocket, token: str):
    if not decode_access_token(token):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    websocket_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_clients.discard(websocket)

