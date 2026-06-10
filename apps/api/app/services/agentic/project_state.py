"""Persist agentic assistant state per project."""
from __future__ import annotations

import json
from datetime import datetime, UTC
from typing import Any

from pydantic import BaseModel, Field

from app.services.project_store import project_dir


class AgenticProjectState(BaseModel):
    project_id: str
    updated_at: str = ""
    user_goal: str | None = None
    selected_test: str | None = None
    selected_fallback_mode: str | None = None
    generated_defaults: dict[str, Any] = Field(default_factory=dict)
    latest_plan: dict[str, Any] | None = None
    latest_inspection: dict[str, Any] | None = None
    candidate_tests: list[str] = Field(default_factory=list)
    chat_summary: str = ""
    last_codegen: dict[str, Any] | None = None
    last_run_id: str | None = None
    latest_report_id: str | None = None
    latest_report_summary: str | None = None
    messages: list[dict[str, Any]] = Field(default_factory=list)


def _state_path(project_id: str):
    return project_dir(project_id) / "agentic_project_state.json"


def load_agentic_state(project_id: str) -> AgenticProjectState | None:
    path = _state_path(project_id)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return AgenticProjectState.model_validate(data)


def save_agentic_state(state: AgenticProjectState) -> AgenticProjectState:
    state.updated_at = datetime.now(UTC).isoformat()
    path = _state_path(state.project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    return state


def update_agentic_state(project_id: str, **fields: Any) -> AgenticProjectState:
    existing = load_agentic_state(project_id)
    if existing is None:
        existing = AgenticProjectState(project_id=project_id)
    for key, value in fields.items():
        if hasattr(existing, key):
            setattr(existing, key, value)
    return save_agentic_state(existing)
