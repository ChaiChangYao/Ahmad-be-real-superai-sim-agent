"""Structured errors for the Agentic Simulation Layer."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgenticErrorResponse(BaseModel):
    error_code: str
    title: str
    explanation: str
    affected_files: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    copyable_debug_details: str = ""


class AgenticError(Exception):
    error_code: str = "agentic_error"
    title: str = "Agentic layer error"
    http_status: int = 422

    def __init__(
        self,
        explanation: str,
        *,
        affected_files: list[str] | None = None,
        suggested_actions: list[str] | None = None,
        debug_details: str = "",
    ) -> None:
        super().__init__(explanation)
        self.explanation = explanation
        self.affected_files = affected_files or []
        self.suggested_actions = suggested_actions or []
        self.debug_details = debug_details

    def to_response(self) -> AgenticErrorResponse:
        return AgenticErrorResponse(
            error_code=self.error_code,
            title=self.title,
            explanation=self.explanation,
            affected_files=self.affected_files,
            suggested_actions=self.suggested_actions,
            copyable_debug_details=self.debug_details,
        )


class MissingRequiredAssetError(AgenticError):
    error_code = "missing_required_asset"
    title = "Required asset missing"


class UnsupportedFileTypeError(AgenticError):
    error_code = "unsupported_file_type"
    title = "Unsupported file type"


class InvalidURDFError(AgenticError):
    error_code = "invalid_urdf"
    title = "Invalid robot description"


class MissingMeshReferenceError(AgenticError):
    error_code = "missing_mesh_reference"
    title = "Missing mesh reference"


class OptionalDependencyMissingError(AgenticError):
    error_code = "optional_dependency_missing"
    title = "Optional feature not available"
    http_status = 503


class UnsafeGenerationError(AgenticError):
    error_code = "unsafe_generation"
    title = "Unsafe automatic generation blocked"


class TestRequirementNotMetError(AgenticError):
    error_code = "test_requirement_not_met"
    title = "Test requirements not met"


def agentic_error_to_dict(exc: AgenticError) -> dict[str, Any]:
    return exc.to_response().model_dump()
