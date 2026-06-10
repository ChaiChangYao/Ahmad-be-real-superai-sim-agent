"""Optional dependency detection and feature flags for the agentic layer."""
from __future__ import annotations

from typing import Any, Literal

DependencyStatus = Literal["available", "missing", "missing_optional"]

CADQUERY_AVAILABLE = False
E2B_AVAILABLE = False
CREWAI_AVAILABLE = False


def _try_import(module: str) -> bool:
    try:
        __import__(module)
        return True
    except ImportError:
        return False


def _probe_optional() -> None:
    global CADQUERY_AVAILABLE, E2B_AVAILABLE, CREWAI_AVAILABLE
    CADQUERY_AVAILABLE = _try_import("cadquery")
    E2B_AVAILABLE = _try_import("e2b")
    CREWAI_AVAILABLE = _try_import("crewai")


_probe_optional()


def check_dependency_status() -> dict[str, DependencyStatus]:
    """Return install status for agentic-layer dependencies."""
    required = {
        "pydantic": "available" if _try_import("pydantic") else "missing",
        "pydantic_ai": "available" if _try_import("pydantic_ai") else "missing",
        "urdfpy": "available" if _try_import("urdfpy") else "missing",
        "trimesh": "available" if _try_import("trimesh") else "missing",
        "numpy": "available" if _try_import("numpy") else "missing",
        "lxml": "available" if _try_import("lxml") else "missing",
        "fastapi": "available" if _try_import("fastapi") else "missing",
    }
    optional = {
        "cadquery": "available" if CADQUERY_AVAILABLE else "missing_optional",
        "e2b": "available" if E2B_AVAILABLE else "missing_optional",
        "crewai": "available" if CREWAI_AVAILABLE else "missing_optional",
    }
    return {**required, **optional}


def get_optional_feature_status() -> dict[str, Any]:
    """Expose feature flags and human-readable messages for optional capabilities."""
    _probe_optional()
    status = check_dependency_status()

    def _msg(name: str, install_hint: str) -> str:
        if status.get(name) == "available":
            return f"{name} is available."
        return f"Feature not available: {install_hint}"

    import os
    from app.services.agentic.execution.e2b_runner import e2b_configured
    from app.services.agentic.execution.runner import backend_available, default_backend
    from app.services.agentic.execution.schemas import ExecutionBackend
    from app.services.agentic.reporting.pydantic_reporter import llm_reporter_enabled

    execution_backends = {
        "local": backend_available(ExecutionBackend.local),
        "docker": backend_available(ExecutionBackend.docker),
        "e2b": e2b_configured(),
    }
    return {
        "CADQUERY_AVAILABLE": CADQUERY_AVAILABLE,
        "E2B_AVAILABLE": E2B_AVAILABLE,
        "CREWAI_AVAILABLE": CREWAI_AVAILABLE,
        "EXECUTION_DEFAULT_BACKEND": default_backend().value,
        "EXECUTION_BACKENDS": execution_backends,
        "BUILDABLES_EXECUTION_BACKEND": os.getenv("BUILDABLES_EXECUTION_BACKEND", "local"),
        "ENABLE_LLM_REPORTER": llm_reporter_enabled(),
        "llm_reporter": "available" if llm_reporter_enabled() else "unavailable",
        "dependencies": status,
        "messages": {
            "cadquery": _msg("cadquery", "install cadquery to enable STEP mesh recovery via CadQuery."),
            "e2b": _msg("e2b", "install e2b and configure API keys for remote sandbox execution."),
            "crewai": _msg("crewai", "install crewai for multi-agent orchestration."),
            "execution_docker": "Docker execution backend is not configured. Use local.",
            "execution_e2b": _msg("e2b", "install e2b and set E2B_API_KEY for cloud sandbox."),
        },
    }
