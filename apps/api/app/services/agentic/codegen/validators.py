"""Validate context and generated scripts before execution."""
from __future__ import annotations

from pathlib import Path

from app.services.agentic.codegen.schemas import (
    GeneratedScriptValidation,
    GenesisScriptContext,
    GenesisTemplateSpec,
)
from app.services.agentic.codegen.safety import validate_output_paths, validate_script_safety


def _field_present(ctx: GenesisScriptContext, field: str) -> bool:
    val = getattr(ctx, field, None)
    if val is None:
        return False
    if isinstance(val, str):
        return bool(val.strip())
    if isinstance(val, list):
        return len(val) > 0
    if isinstance(val, dict):
        return bool(val)
    return True


def validate_context(ctx: GenesisScriptContext, spec: GenesisTemplateSpec) -> list[str]:
    errors: list[str] = []
    for field in spec.required_context_fields:
        if not _field_present(ctx, field):
            errors.append(f"Missing required context field: {field}")

    if spec.supports_robot and ctx.test_id not in {"static_mesh_preview"}:
        if not ctx.robot_description_path and ctx.fallback_mode != "static_mesh":
            errors.append("robot_description_path is required for robot tests")

    if spec.test_id == "static_mesh_preview" and not ctx.mesh_assets:
        errors.append("mesh_assets required for static mesh preview")

    if ctx.fallback_mode == "skeleton" and not ctx.robot_description_path:
        errors.append("Skeleton fallback requires a generated URDF path")

    return errors


def validate_required_files(ctx: GenesisScriptContext) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if ctx.robot_description_path:
        p = Path(ctx.robot_description_path)
        if not p.is_file():
            errors.append(f"Robot description not found: {ctx.robot_description_path}")
    for mesh in ctx.mesh_assets:
        mp = mesh.get("path") or mesh.get("relative")
        if mp and not Path(mp).is_file():
            errors.append(f"Mesh asset not found: {mp}")
    return len(errors) == 0, errors


def validate_generated_script(
    source: str,
    ctx: GenesisScriptContext,
    spec: GenesisTemplateSpec,
) -> GeneratedScriptValidation:
    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(validate_context(ctx, spec))
    files_ok, file_errors = validate_required_files(ctx)
    errors.extend(file_errors)

    safety_errors, safety_warnings = validate_script_safety(source)
    errors.extend(safety_errors)
    warnings.extend(safety_warnings)
    errors.extend(validate_output_paths(ctx.model_dump(), Path(ctx.project_root)))

    expected = list(spec.outputs)
    if ctx.replay_config.record_visual:
        expected.append("state_timeseries")
    if ctx.replay_config.record_telemetry:
        expected.append("telemetry_timeseries")

    unsafe = [e for e in safety_errors if "Banned" in e or "not allowed" in e]

    return GeneratedScriptValidation(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings + ctx.warnings,
        blocked_reason=errors[0] if errors else "",
        unsafe_patterns_found=unsafe,
        required_files_present=files_ok,
        expected_outputs=list(dict.fromkeys(expected)),
    )
