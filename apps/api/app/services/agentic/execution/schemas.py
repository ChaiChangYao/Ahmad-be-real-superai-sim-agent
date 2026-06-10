"""Execution layer Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionBackend(str, Enum):
    local = "local"
    docker = "docker"
    e2b = "e2b"


class RunStatus(str, Enum):
    queued = "queued"
    preparing = "preparing"
    validating = "validating"
    running = "running"
    recording = "recording"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    timed_out = "timed_out"


class ExecutionRequest(BaseModel):
    project_id: str
    script_id: str
    backend: ExecutionBackend = ExecutionBackend.local
    mode: str = "web"
    test_id: str = ""
    run_label: str = ""
    timeout_seconds: int = 300
    env_overrides: dict[str, str] = Field(default_factory=dict)
    allow_fallback_backend: bool = False
    user_parameters: dict[str, Any] = Field(default_factory=dict)


class RunArtifact(BaseModel):
    artifact_id: str
    run_id: str
    kind: str
    path: str = ""
    url: str = ""
    size_bytes: int = 0
    content_type: str = ""
    created_at: str = ""


class ExecutionRun(BaseModel):
    run_id: str
    project_id: str
    script_id: str = ""
    test_id: str = ""
    template_id: str = ""
    backend: ExecutionBackend = ExecutionBackend.local
    status: RunStatus = RunStatus.queued
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None
    run_dir: str = ""
    command: list[str] = Field(default_factory=list)
    pid: int | None = None
    exit_code: int | None = None
    timeout_seconds: int = 300
    stdout_path: str = ""
    stderr_path: str = ""
    combined_log_path: str = ""
    manifest_path: str = ""
    replay_path: str = ""
    telemetry_path: str = ""
    report_path: str = ""
    error_summary: str = ""
    warning_summary: str = ""
    artifacts: list[RunArtifact] = Field(default_factory=list)
    failure: dict[str, Any] | None = None


class RunEvent(BaseModel):
    run_id: str
    ts: str
    level: str = "info"
    source: str = "worker"
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class ExecutionFailure(BaseModel):
    error_code: str
    title: str
    explanation: str
    traceback_path: str = ""
    affected_files: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    raw_excerpt: str = ""
    copyable_debug_details: str = ""
