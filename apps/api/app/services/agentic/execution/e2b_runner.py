"""E2B cloud sandbox backend — optional stub."""
from __future__ import annotations

import os

from app.services.agentic.dependencies import E2B_AVAILABLE
from app.services.agentic.execution.errors import BackendUnavailableError
from app.services.agentic.execution.schemas import ExecutionRequest, ExecutionRun


def e2b_configured() -> bool:
    return E2B_AVAILABLE and bool(os.getenv("E2B_API_KEY"))


def run_generated_script_e2b(request: ExecutionRequest, run: ExecutionRun) -> ExecutionRun:
    if not E2B_AVAILABLE:
        raise BackendUnavailableError(
            "E2B SDK is not installed. pip install e2b to enable cloud sandbox execution.",
            suggested_actions=["Use local backend", "pip install e2b"],
        )
    if not os.getenv("E2B_API_KEY"):
        raise BackendUnavailableError(
            "E2B API key is not configured. Set E2B_API_KEY or use local backend.",
            suggested_actions=["Use local backend", "Configure E2B_API_KEY in environment"],
        )
    raise BackendUnavailableError(
        "E2B Genesis execution is not verified in MVP. Full Genesis GPU/graphics support in E2B is unconfirmed.",
        suggested_actions=["Use local backend for Genesis simulations"],
    )
