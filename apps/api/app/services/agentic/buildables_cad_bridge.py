"""Bridge stub for future Pillar 1 CAD generation — honest not-implemented responses."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.services.agentic.schemas import MeshReference


class CadBridgeResult(BaseModel):
    status: str = "not_implemented"  # not_implemented | stub_queued | completed
    request_type: str = ""
    explanation: str = ""
    queued_items: list[str] = Field(default_factory=list)


_STUB_MESSAGE = (
    "Buildables CAD generation bridge is not connected yet. "
    "For now, upload a robot zip with meshes/, use STEP recovery, or accept skeleton fallback."
)


def request_missing_mesh_generation(project_id: str, missing_meshes: list[MeshReference]) -> CadBridgeResult:
    paths = [m.raw_path for m in missing_meshes[:20]]
    return CadBridgeResult(
        status="not_implemented",
        request_type="missing_mesh_generation",
        explanation=_STUB_MESSAGE,
        queued_items=paths,
    )


def request_collision_mesh_generation(project_id: str) -> CadBridgeResult:
    return CadBridgeResult(
        status="not_implemented",
        request_type="collision_mesh_generation",
        explanation=_STUB_MESSAGE,
    )


def request_sensor_mount_generation(project_id: str, sensor_type: str) -> CadBridgeResult:
    return CadBridgeResult(
        status="not_implemented",
        request_type="sensor_mount_generation",
        explanation=f"{_STUB_MESSAGE} (sensor: {sensor_type})",
        queued_items=[sensor_type],
    )


def request_material_metadata(project_id: str) -> CadBridgeResult:
    return CadBridgeResult(
        status="not_implemented",
        request_type="material_metadata",
        explanation=_STUB_MESSAGE,
    )


def request_boundary_conditions(project_id: str, test_type: str) -> CadBridgeResult:
    return CadBridgeResult(
        status="not_implemented",
        request_type="boundary_conditions",
        explanation=f"{_STUB_MESSAGE} (test: {test_type})",
        queued_items=[test_type],
    )
