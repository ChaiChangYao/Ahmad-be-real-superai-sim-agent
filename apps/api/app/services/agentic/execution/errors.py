"""Execution layer errors."""
from __future__ import annotations

from app.services.agentic.execution.schemas import ExecutionFailure


class ExecutionError(Exception):
    error_code: str = "execution_error"
    title: str = "Execution error"
    http_status: int = 422

    def __init__(
        self,
        explanation: str,
        *,
        suggested_actions: list[str] | None = None,
        affected_files: list[str] | None = None,
        debug_details: str = "",
    ) -> None:
        super().__init__(explanation)
        self.explanation = explanation
        self.suggested_actions = suggested_actions or []
        self.affected_files = affected_files or []
        self.debug_details = debug_details

    def to_failure(self) -> ExecutionFailure:
        return ExecutionFailure(
            error_code=self.error_code,
            title=self.title,
            explanation=self.explanation,
            affected_files=self.affected_files,
            suggested_actions=self.suggested_actions,
            copyable_debug_details=self.debug_details,
        )


class BackendUnavailableError(ExecutionError):
    error_code = "backend_unavailable"
    title = "Execution backend unavailable"


class RunNotFoundError(ExecutionError):
    error_code = "run_not_found"
    title = "Run not found"
    http_status = 404


class UnsafeScriptError(ExecutionError):
    error_code = "unsafe_script"
    title = "Script failed safety validation"


class RunAlreadyActiveError(ExecutionError):
    error_code = "run_already_active"
    title = "A simulation is already running"
