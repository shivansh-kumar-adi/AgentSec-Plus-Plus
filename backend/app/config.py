from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)

PRODUCTION_FRONTEND_ORIGIN = "https://agentsec-ai.vercel.app"
LOCAL_FRONTEND_ORIGIN = "http://localhost:5173"


def _cors_origins() -> tuple[str, ...]:
    configured = (
        item.strip()
        for item in os.getenv("AGENTSEC_CORS_ORIGINS", LOCAL_FRONTEND_ORIGIN).split(",")
    )
    return tuple(dict.fromkeys((*filter(None, configured), LOCAL_FRONTEND_ORIGIN, PRODUCTION_FRONTEND_ORIGIN)))


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("AGENTSEC_ENV", "development")
    database_url: str | None = os.getenv("DATABASE_URL") or None
    database_path: str = os.getenv("AGENTSEC_DATABASE_PATH", "agentsec.db")
    secret_key: str = os.getenv("AGENTSEC_SECRET_KEY", "development-only-change-me-32-bytes")
    bootstrap_admin: str = os.getenv("AGENTSEC_BOOTSTRAP_ADMIN", "admin")
    bootstrap_password: str = os.getenv("AGENTSEC_BOOTSTRAP_PASSWORD", "change-me-in-production")
    cors_origins: tuple[str, ...] = _cors_origins()
    llm_provider: str = os.getenv("AGENTSEC_LLM_PROVIDER", "disabled")
    llm_api_key: str = os.getenv("AGENTSEC_LLM_API_KEY", "")

    def validate(self) -> None:
        if self.environment == "production":
            if len(self.secret_key) < 32 or "change" in self.secret_key.lower():
                raise RuntimeError("AGENTSEC_SECRET_KEY must be a strong production secret")
            if len(self.bootstrap_password) < 12 or "change" in self.bootstrap_password.lower():
                raise RuntimeError("Bootstrap password must be strong and changed in production")
            if not self.bootstrap_admin.strip():
                raise RuntimeError("AGENTSEC_BOOTSTRAP_ADMIN must not be empty")


settings = Settings()

