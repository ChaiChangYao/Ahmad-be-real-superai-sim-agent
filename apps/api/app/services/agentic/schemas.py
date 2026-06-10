"""Typed Pydantic schemas for the Agentic Simulation Layer."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


AssetRole = Literal[
    "robot_description",
    "mesh",
    "cad",
    "texture",
    "control_script",
    "metadata",
    "unknown",
]
AssetSource = Literal["user_upload", "generated", "recovered", "catalogue"]
AssetStatus = Literal["found", "missing", "unsupported", "generated", "failed"]
RobotFormat = Literal["urdf", "mjcf", "unknown"]
MeshUsage = Literal["visual", "collision", "both"]
TestCategory = Literal[
    "rigid",
    "robot_motion",
    "sensor",
    "telemetry",
    "cfd_readiness",
    "fea_readiness",
    "thermal",
    "custom",
]
TestSpecStatus = Literal["available", "blocked", "readiness_only", "not_implemented"]
ExecutionStatus = Literal["queued", "running", "completed", "failed"]
PassFail = Literal["pass", "fail", "inconclusive", "readiness_only"]


class UploadedAsset(BaseModel):
    id: str
    project_id: str
    original_filename: str
    stored_path: str
    relative_path: str
    file_type: str
    size_bytes: int
    sha256: str
    role: AssetRole = "unknown"
    source: AssetSource = "user_upload"
    status: AssetStatus = "found"


class MeshReference(BaseModel):
    source_file: str = ""
    usage: MeshUsage = "visual"
    raw_path: str
    resolved_path: str = ""
    package_name: str = ""
    file_type: str = "unknown"
    exists: bool = False
    status: AssetStatus = "missing"
    matched_uploaded_asset_id: str | None = None
    action_needed: str = ""


class RobotDescriptionInspection(BaseModel):
    parsed: bool = False
    format: RobotFormat = "unknown"
    source_path: str = ""
    links_count: int = 0
    joints_count: int = 0
    movable_joints_count: int = 0
    fixed_joints_count: int = 0
    root_link: str = ""
    link_names: list[str] = Field(default_factory=list)
    joint_names: list[str] = Field(default_factory=list)
    mesh_references: list[MeshReference] = Field(default_factory=list)
    has_inertial_data: bool = False
    has_joint_limits: bool = False
    has_collision_geometry: bool = False
    has_visual_geometry: bool = False
    detected_sensors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class MeshInspection(BaseModel):
    asset_id: str = ""
    path: str = ""
    parsed: bool = False
    file_type: str = "unknown"
    watertight: bool | None = None
    volume: float | None = None
    bounds: list[float] | None = None  # [min_x, min_y, min_z, max_x, max_y, max_z]
    center_mass: list[float] | None = None
    face_count: int | None = None
    vertex_count: int | None = None
    units_guess: str = "unknown"
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SimulationTestSpec(BaseModel):
    test_id: str
    display_name: str
    category: TestCategory
    description: str
    required_inputs: list[str] = Field(default_factory=list)
    optional_inputs: list[str] = Field(default_factory=list)
    generatable_inputs: list[str] = Field(default_factory=list)
    cannot_fake_inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    viewer_layout: str = "simulation_only"
    telemetry_schema: dict[str, Any] = Field(default_factory=dict)
    genesis_template: str = ""
    supported_asset_types: list[str] = Field(default_factory=list)
    status: TestSpecStatus = "available"


class TestReadinessResult(BaseModel):
    test_id: str
    can_run: bool = False
    can_run_with_fallback: bool = False
    confidence: float = 0.0
    missing_required: list[str] = Field(default_factory=list)
    missing_optional: list[str] = Field(default_factory=list)
    generated_defaults_available: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    required_user_questions: list[str] = Field(default_factory=list)
    fallback_modes: list[str] = Field(default_factory=list)


class SimulationPlan(BaseModel):
    project_id: str
    user_goal: str | None = None
    asset_summary: dict[str, Any] = Field(default_factory=dict)
    recommended_tests: list[TestReadinessResult] = Field(default_factory=list)
    blocked_tests: list[TestReadinessResult] = Field(default_factory=list)
    required_questions: list[str] = Field(default_factory=list)
    generation_tasks: list[str] = Field(default_factory=list)
    selected_test: str | None = None
    plan_steps: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    agent_explanation: str = ""


class GeneratedSimulationScript(BaseModel):
    script_id: str
    project_id: str
    test_id: str
    script_path: str
    template_used: str
    inputs_used: dict[str, Any] = Field(default_factory=dict)
    generated_files: list[str] = Field(default_factory=list)
    safety_checks: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    run_id: str
    status: ExecutionStatus = "queued"
    command: str = ""
    stdout_path: str = ""
    stderr_path: str = ""
    replay_path: str = ""
    telemetry_path: str = ""
    report_path: str = ""
    exit_code: int | None = None
    error_summary: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None


class RecoveryResult(BaseModel):
    success: bool = False
    generated_files: list[str] = Field(default_factory=list)
    failed_files: list[str] = Field(default_factory=list)
    requires_user_mapping: bool = False
    explanation: str = ""
    dependency_status: str = "available"


class ProjectInspectionReport(BaseModel):
    project_id: str
    assets: list[UploadedAsset] = Field(default_factory=list)
    robot_descriptions: list[RobotDescriptionInspection] = Field(default_factory=list)
    mesh_inspections: list[MeshInspection] = Field(default_factory=list)
    missing_mesh_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class TestRequirementsResponse(BaseModel):
    project_id: str
    specs: list[SimulationTestSpec] = Field(default_factory=list)
    readiness: list[TestReadinessResult] = Field(default_factory=list)


# Re-export rich report schema (import at module end to avoid circular imports).
from app.services.agentic.reporting.schemas import EngineeringReport as EngineeringReport  # noqa: E402,F401
