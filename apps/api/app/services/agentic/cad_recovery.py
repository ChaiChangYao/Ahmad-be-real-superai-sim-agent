"""Optional STEP/CAD recovery — honest stubs with FreeCAD delegation."""
from __future__ import annotations

from pathlib import Path

from app.services.agentic.dependencies import CADQUERY_AVAILABLE
from app.services.agentic.errors import OptionalDependencyMissingError
from app.services.agentic.file_inventory import find_assets_by_role, load_asset_inventory
from app.services.agentic.schemas import MeshReference, RecoveryResult, UploadedAsset
from app.services.agentic.urdf_inspector import inspect_all_robot_descriptions
from app.services.cad_import.step_importer import step_converter_available
from app.services.cad_import.step_mesh_converter import (
    converter_status,
    export_mapped_meshes,
    export_whole_step_preview,
    find_project_step_file,
    inspect_step_parts,
    suggest_step_mappings,
)
from app.services.importers.asset_resolver import normalize_mesh_ref
from app.services.project_store import project_dir


def can_recover_from_step(project_id: str) -> bool:
    """True if STEP exists and FreeCAD or CadQuery is available."""
    pdir = project_dir(project_id)
    step = find_project_step_file(pdir)
    if step is None:
        return False
    return step_converter_available() or CADQUERY_AVAILABLE


def list_step_files(project_id: str) -> list[UploadedAsset]:
    assets = load_asset_inventory(project_id)
    return find_assets_by_role(assets, "cad")


def _freecad_available() -> bool:
    return step_converter_available()


def attempt_step_static_preview(project_id: str) -> RecoveryResult:
    """Export whole STEP assembly as static preview STL."""
    pdir = project_dir(project_id)
    step_path = find_project_step_file(pdir)
    if step_path is None:
        return RecoveryResult(
            success=False,
            explanation="No STEP file found in project assets.",
            dependency_status="available",
        )

    if not _freecad_available() and not CADQUERY_AVAILABLE:
        return RecoveryResult(
            success=False,
            explanation="Feature not available: install FreeCAD (freecadcmd on PATH) or cadquery to enable STEP preview.",
            dependency_status="missing_optional_dependency",
        )

    if not _freecad_available():
        return RecoveryResult(
            success=False,
            explanation=(
                "CadQuery is installed but whole-assembly preview uses FreeCAD in Part 1. "
                "Install FreeCAD CLI for static STEP preview."
            ),
            dependency_status="missing_optional_dependency",
        )

    out_dir = pdir / "generated" / "step_preview"
    out_path = out_dir / "whole_assembly.stl"
    try:
        export_whole_step_preview(step_path, out_path)
        return RecoveryResult(
            success=True,
            generated_files=[str(out_path)],
            requires_user_mapping=True,
            explanation=(
                "Generated static preview mesh from STEP. "
                "Can generate static preview, but cannot recover per-link URDF meshes without part mapping."
            ),
            dependency_status="available",
        )
    except Exception as exc:
        return RecoveryResult(
            success=False,
            failed_files=[str(step_path)],
            explanation=f"STEP preview export failed: {exc}",
            dependency_status="available",
        )


def attempt_generate_missing_meshes_from_step(
    project_id: str,
    missing_meshes: list[MeshReference],
    *,
    mappings: dict[str, str] | None = None,
) -> RecoveryResult:
    """Attempt per-mesh recovery from STEP with user or suggested mappings."""
    pdir = project_dir(project_id)
    step_path = find_project_step_file(pdir)
    if step_path is None:
        return RecoveryResult(
            success=False,
            explanation="No STEP file found in project.",
            dependency_status="available",
        )

    if not _freecad_available():
        raise OptionalDependencyMissingError(
            "Feature not available: install FreeCAD (freecadcmd on PATH) to generate meshes from STEP.",
            suggested_actions=[
                "Install FreeCAD and ensure freecadcmd is on PATH.",
                "Alternatively upload STL/OBJ mesh files directly.",
            ],
        )

    robot_descs = inspect_all_robot_descriptions(project_id)
    urdf_path: Path | None = None
    for desc in robot_descs:
        if desc.parsed and desc.source_path:
            urdf_path = Path(desc.source_path)
            break

    if urdf_path is None:
        return RecoveryResult(
            success=False,
            explanation="No URDF found — cannot map STEP parts to URDF mesh paths.",
            requires_user_mapping=True,
            dependency_status="available",
        )

    missing_refs = [m.raw_path for m in missing_meshes if m.status == "missing"]
    if not missing_refs:
        missing_refs = [m.raw_path for m in missing_meshes]

    inspect = inspect_step_parts(step_path)
    parts = [p.get("name", "") for p in inspect.get("parts", []) if p.get("name")]

    if len(parts) <= 1 and len(missing_refs) > 1:
        return RecoveryResult(
            success=False,
            requires_user_mapping=True,
            explanation=(
                "STEP appears to be one monolithic model and cannot map to per-link URDF mesh filenames "
                "without part mapping. Use static preview or provide explicit part-to-mesh mappings."
            ),
            dependency_status="available",
        )

    effective_mappings = dict(mappings or {})
    if not effective_mappings:
        suggestions = suggest_step_mappings(missing_refs, parts)
        for row in suggestions:
            ref = row.get("urdf_mesh_path")
            part = row.get("suggested_step_part")
            if ref and part:
                effective_mappings[str(ref)] = str(part)

    if not effective_mappings:
        return RecoveryResult(
            success=False,
            requires_user_mapping=True,
            explanation=(
                "Cannot auto-map STEP parts to URDF mesh paths. "
                "Provide explicit mappings via the recovery API."
            ),
            dependency_status="available",
        )

    try:
        result = export_mapped_meshes(pdir, urdf_path, step_path, effective_mappings)
        generated = [row["output_path"] for row in result.get("exported", [])]
        failed = result.get("errors", [])
        return RecoveryResult(
            success=len(generated) > 0,
            generated_files=generated,
            failed_files=failed,
            requires_user_mapping=len(failed) > 0,
            explanation=(
                f"Exported {len(generated)} mesh file(s) from STEP. "
                + ("Some mappings failed — verify part names." if failed else "All mapped meshes generated.")
            ),
            dependency_status="available",
        )
    except Exception as exc:
        return RecoveryResult(
            success=False,
            explanation=f"STEP mesh generation failed: {exc}",
            dependency_status="available",
        )


def cad_recovery_status(project_id: str) -> dict:
    return {
        **converter_status(),
        "cadquery_available": CADQUERY_AVAILABLE,
        "can_recover": can_recover_from_step(project_id),
        "step_files": [a.relative_path for a in list_step_files(project_id)],
    }
