"""Codegen-specific Pydantic schemas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GenesisTemplateSpec(BaseModel):
    template_id: str
    display_name: str
    test_id: str
    category: str
    template_path: str
    required_context_fields: list[str] = Field(default_factory=list)
    optional_context_fields: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    supports_robot: bool = True
    supports_rigid_mesh: bool = False
    supports_sensors: bool = False
    supports_telemetry: bool = False
    notes: str = ""


class SensorConfig(BaseModel):
    sensor_type: str = ""
    attach_link: str = ""
    pose: dict[str, Any] = Field(default_factory=dict)
    sample_rate: float = 100.0
    channels: list[str] = Field(default_factory=list)
    resolution: list[int] = Field(default_factory=lambda: [640, 480])
    fov: float = 60.0
    grid_bounds: list[float] = Field(default_factory=list)
    grid_resolution: int = 16
    heat_source: dict[str, Any] = Field(default_factory=dict)
    contact_links: list[str] = Field(default_factory=list)
    defaults_used: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class PhysicsConfig(BaseModel):
    gravity: list[float] = Field(default_factory=lambda: [0.0, 0.0, -9.81])
    timestep: float = 0.01
    substeps: int = 1
    duration_seconds: float = 4.0
    target_fps: float = 24.0
    friction: float = 0.5
    restitution: float = 0.1
    density: float = 1000.0
    fixed_base: bool = False
    initial_pose: dict[str, Any] = Field(default_factory=dict)
    collision_mode: str = "default"


class ReplayConfig(BaseModel):
    record_visual: bool = True
    record_telemetry: bool = False
    output_state_timeseries_path: str = ""
    output_telemetry_timeseries_path: str = ""
    target_fps: float = 24.0
    smooth_preview: bool = True
    preserve_holds: bool = True
    trim_dead_sections: bool = True


class GenesisScriptContext(BaseModel):
    project_id: str
    test_id: str
    template_id: str = ""
    project_root: str
    asset_root: str
    output_root: str
    script_id: str = ""
    robot_description_path: str = ""
    robot_description_type: str = ""
    mesh_assets: list[dict[str, str]] = Field(default_factory=list)
    selected_links: list[str] = Field(default_factory=list)
    selected_joints: list[str] = Field(default_factory=list)
    joint_limits: dict[str, dict[str, float]] = Field(default_factory=dict)
    fallback_mode: str | None = None
    sensor_config: SensorConfig = Field(default_factory=SensorConfig)
    physics_config: PhysicsConfig = Field(default_factory=PhysicsConfig)
    render_config: dict[str, Any] = Field(default_factory=dict)
    telemetry_config: dict[str, Any] = Field(default_factory=dict)
    replay_config: ReplayConfig = Field(default_factory=ReplayConfig)
    generated_defaults: dict[str, Any] = Field(default_factory=dict)
    user_parameters: dict[str, Any] = Field(default_factory=dict)
    safety_flags: dict[str, bool] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    link_names: list[str] = Field(default_factory=list)
    missing_mesh_count: int = 0


class GeneratedScriptValidation(BaseModel):
    valid: bool = False
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blocked_reason: str = ""
    unsafe_patterns_found: list[str] = Field(default_factory=list)
    required_files_present: bool = False
    expected_outputs: list[str] = Field(default_factory=list)


class CodeGenResult(BaseModel):
    success: bool = False
    script_id: str = ""
    script_path: str = ""
    context_path: str = ""
    template_id: str = ""
    context: GenesisScriptContext | None = None
    validation: GeneratedScriptValidation = Field(default_factory=GeneratedScriptValidation)
    expected_outputs: list[str] = Field(default_factory=list)
    next_step: str = ""
    explanation: str = ""
