from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class AgentCreate(BaseModel):
    name: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,64}$")
    platform: Literal["windows", "linux"]


class SecurityEventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(min_length=8, max_length=128)
    event_type: Literal["process", "network_connection", "authentication", "file_change", "detection"]
    occurred_at: datetime
    severity: int = Field(ge=0, le=10)
    source_ip: str | None = Field(default=None, max_length=45)
    process_id: int | None = Field(default=None, ge=0)
    username: str | None = Field(default=None, max_length=128)
    description: str = Field(min_length=1, max_length=1024)
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("attributes")
    @classmethod
    def bound_attributes(cls, value: dict[str, Any]) -> dict[str, Any]:
        if len(value) > 50 or len(str(value)) > 16_384:
            raise ValueError("attributes exceed ingestion limits")
        return value


class InvestigationRequest(BaseModel):
    incident_id: int = Field(gt=0)


class ActionRequest(BaseModel):
    incident_id: int = Field(gt=0)
    action_type: Literal["block_ip", "terminate_process", "quarantine_file", "disable_account", "notify"]
    target: str = Field(min_length=1, max_length=512)
    parameters: dict[str, Any] = Field(default_factory=dict)
    simulation: bool = True

