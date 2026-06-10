"""Dev-only LLM / OpenRouter settings (optional polish — not required for agentic flow)."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["settings"])

_API_ROOT = Path(__file__).resolve().parents[2]
_ENV_LOCAL = _API_ROOT / ".env.local"


class LlmSettings(BaseModel):
    enable_llm_assistant: bool = False
    enable_llm_reporter: bool = False
    openrouter_api_key_set: bool = False
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o-mini"


class LlmSettingsUpdate(BaseModel):
    enable_llm_assistant: bool | None = None
    enable_llm_reporter: bool | None = None
    openrouter_api_key: str | None = Field(default=None, description="Stored locally in apps/api/.env.local for dev")
    openrouter_base_url: str | None = None
    openrouter_model: str | None = None


def _read_env_local() -> dict[str, str]:
    if not _ENV_LOCAL.is_file():
        return {}
    out: dict[str, str] = {}
    for line in _ENV_LOCAL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        out[key.strip()] = val.strip()
    return out


def _write_env_local(updates: dict[str, str]) -> None:
    existing = _read_env_local()
    existing.update(updates)
    lines = [f"{k}={v}" for k, v in sorted(existing.items())]
    _ENV_LOCAL.write_text("\n".join(lines) + "\n", encoding="utf-8")


@router.get("/settings/llm")
def get_llm_settings() -> dict:
    key = os.getenv("OPENROUTER_API_KEY", "")
    return LlmSettings(
        enable_llm_assistant=os.getenv("ENABLE_LLM_ASSISTANT", "0").lower() in ("1", "true", "yes"),
        enable_llm_reporter=os.getenv("ENABLE_LLM_REPORTER", "0").lower() in ("1", "true", "yes"),
        openrouter_api_key_set=bool(key),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
    ).model_dump()


@router.put("/settings/llm")
def put_llm_settings(body: LlmSettingsUpdate) -> dict:
    updates: dict[str, str] = {}
    if body.enable_llm_assistant is not None:
        updates["ENABLE_LLM_ASSISTANT"] = "1" if body.enable_llm_assistant else "0"
        os.environ["ENABLE_LLM_ASSISTANT"] = updates["ENABLE_LLM_ASSISTANT"]
    if body.enable_llm_reporter is not None:
        updates["ENABLE_LLM_REPORTER"] = "1" if body.enable_llm_reporter else "0"
        os.environ["ENABLE_LLM_REPORTER"] = updates["ENABLE_LLM_REPORTER"]
    if body.openrouter_api_key is not None:
        if body.openrouter_api_key.strip():
            updates["OPENROUTER_API_KEY"] = body.openrouter_api_key.strip()
            os.environ["OPENROUTER_API_KEY"] = updates["OPENROUTER_API_KEY"]
        else:
            updates["OPENROUTER_API_KEY"] = ""
            os.environ.pop("OPENROUTER_API_KEY", None)
    if body.openrouter_base_url:
        updates["OPENROUTER_BASE_URL"] = body.openrouter_base_url
        os.environ["OPENROUTER_BASE_URL"] = body.openrouter_base_url
    if body.openrouter_model:
        updates["OPENROUTER_MODEL"] = body.openrouter_model
        os.environ["OPENROUTER_MODEL"] = body.openrouter_model
    if not updates:
        raise HTTPException(status_code=400, detail="No settings to update")
    try:
        _write_env_local(updates)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not write .env.local: {exc}") from exc
    return get_llm_settings()
