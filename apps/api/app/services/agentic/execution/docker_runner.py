"""Docker execution backend — stub until Docker image is configured."""
from __future__ import annotations

from app.services.agentic.execution.errors import BackendUnavailableError
from app.services.agentic.execution.schemas import ExecutionRequest, ExecutionRun


def run_generated_script_docker(request: ExecutionRequest, run: ExecutionRun) -> ExecutionRun:
    raise BackendUnavailableError(
        "Docker execution backend is not configured. Use local backend or configure Docker.",
        suggested_actions=[
            "Set BUILDABLES_EXECUTION_BACKEND=local",
            "Configure a Genesis-compatible Docker image for production isolation",
        ],
    )
