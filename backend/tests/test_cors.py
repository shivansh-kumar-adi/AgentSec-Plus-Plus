import os

os.environ.setdefault("AGENTSEC_DATABASE_PATH", "test-agentsec.db")
os.environ.setdefault("DATABASE_URL", "")
os.environ["AGENTSEC_SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes"
os.environ["AGENTSEC_BOOTSTRAP_PASSWORD"] = "correct-horse-battery-staple"

from fastapi.testclient import TestClient

from app.main import app


ALLOWED_ORIGIN = "https://agentsec-ai.vercel.app"
UNAPPROVED_ORIGIN = "https://unapproved.example"


def test_login_preflight_allows_production_frontend():
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    methods = {item.strip() for item in response.headers["access-control-allow-methods"].split(",")}
    assert {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"} <= methods
    headers = {item.strip().lower() for item in response.headers["access-control-allow-headers"].split(",")}
    assert {"content-type", "authorization"} <= headers


def test_login_authentication_error_includes_cors_header():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            headers={"Origin": ALLOWED_ORIGIN},
            json={"username": "invalid-user", "password": "invalid-password"},
        )

    assert response.status_code == 401
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


def test_unapproved_origin_is_not_granted_cors_access():
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": UNAPPROVED_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization",
            },
        )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
