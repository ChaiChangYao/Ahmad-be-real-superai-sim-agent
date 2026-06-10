"""Dispatch execution to configured backend."""
from __future__ import annotations

import os

from app.services.agentic.execution.docker_runner import run_generated_script_docker
from app.services.agentic.execution.e2b_runner import e2b_configured, run_generated_script_e2b
from app.services.agentic.execution.errors import BackendUnavailableError, ExecutionError
from app.services.agentic.execution.process_manager import start_run_async
from app.services.agentic.execution.run_store import create_run_record
from app.services.agentic.execution.schemas import ExecutionBackend, ExecutionRequest, ExecutionRun


def default_backend() -> ExecutionBackend:
    raw = os.getenv("BUILDABLES_EXECUTION_BACKEND", "local").lower()
    try:
        return ExecutionBackend(raw)
    except ValueError:
        return ExecutionBackend.local


def backend_available(backend: ExecutionBackend) -> bool:
    if backend == ExecutionBackend.local:
        return True
    if backend == ExecutionBackend.docker:
        return False
    if backend == ExecutionBackend.e2b:
        return e2b_configured()
    return False


def start_run(request: ExecutionRequest) -> ExecutionRun:
    backend = request.backend or default_backend()
    if not backend_available(backend):
        if request.allow_fallback_backend and backend != ExecutionBackend.local:
            backend = ExecutionBackend.local
        else:
            raise BackendUnavailableError(
                f"Execution backend '{backend.value}' is not available.",
                suggested_actions=[
                    "Set BUILDABLES_EXECUTION_BACKEND=local",
                    "Configure Docker or E2B if required",
                ],
            )

    run = create_run_record(
        request.project_id,
        request.script_id,
        test_id=request.test_id,
        backend=backend.value,
        timeout_seconds=request.timeout_seconds,
    )

    try:
        if backend == ExecutionBackend.local:
            return start_run_async(request, run)
        if backend == ExecutionBackend.docker:
            return run_generated_script_docker(request, run)
        if backend == ExecutionBackend.e2b:
            return run_generated_script_e2b(request, run)
    except ExecutionError:
        raise
    raise BackendUnavailableError(f"Unknown backend: {backend}")
