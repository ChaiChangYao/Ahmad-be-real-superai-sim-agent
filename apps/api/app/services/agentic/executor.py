"""Thin wrapper — delegates to execution.runner."""
from __future__ import annotations

from app.services.agentic.execution.process_manager import get_run_status
from app.services.agentic.execution.runner import start_run
from app.services.agentic.execution.schemas import ExecutionBackend, ExecutionRequest
from app.services.agentic.schemas import ExecutionResult


def execute_simulation(
    project_id: str,
    script_id: str,
    *,
    test_id: str = "",
    timeout_seconds: int = 300,
) -> ExecutionResult:
    request = ExecutionRequest(
        project_id=project_id,
        script_id=script_id,
        test_id=test_id,
        backend=ExecutionBackend.local,
        timeout_seconds=timeout_seconds,
    )
    run = start_run(request)
    refreshed = get_run_status(project_id, run.run_id)
    return ExecutionResult(
        run_id=refreshed.run_id,
        status=refreshed.status.value,
        command=" ".join(refreshed.command),
        stdout_path=refreshed.stdout_path,
        stderr_path=refreshed.stderr_path,
        replay_path=refreshed.replay_path,
        telemetry_path=refreshed.telemetry_path,
        report_path=refreshed.report_path,
        exit_code=refreshed.exit_code,
        error_summary=refreshed.error_summary or "",
    )
