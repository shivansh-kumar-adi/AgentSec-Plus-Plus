from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from .config import settings


def hash_password(password: str, salt: bytes | None = None) -> str:
    if len(password) < 12:
        raise ValueError("password must contain at least 12 characters")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"pbkdf2_sha256$310000${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_text)
        expected = base64.urlsafe_b64decode(digest_text)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(rounds))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def create_access_token(user_id: int, role: str, ttl_seconds: int = 3600) -> str:
    payload = {"sub": user_id, "role": role, "exp": int(time.time()) + ttl_seconds,
               "nonce": secrets.token_urlsafe(8)}
    body = _encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = _encode(hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{signature}"


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        body, supplied = token.split(".", 1)
        expected = _encode(hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(supplied, expected):
            return None
        payload = json.loads(_decode(body))
        if int(payload["exp"]) < int(time.time()):
            return None
        return payload
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def new_agent_secret() -> str:
    return secrets.token_urlsafe(32)


def hash_agent_secret(secret: str) -> str:
    return hmac.new(settings.secret_key.encode(), secret.encode(), hashlib.sha256).hexdigest()


def verify_agent_signature(secret: str, timestamp: str, nonce: str, body: bytes, supplied: str) -> bool:
    body_hash = hashlib.sha256(body).hexdigest()
    message = f"{timestamp}\n{nonce}\n{body_hash}".encode()
    expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, supplied)

