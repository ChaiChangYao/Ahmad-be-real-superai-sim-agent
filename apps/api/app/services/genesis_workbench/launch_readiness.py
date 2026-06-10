from __future__ import annotations

import json
from pathlib import Path

from app.services.genesis.genesis_runtime import genesis_runtime
from app.services.genesis.imported_robot_loader import resolve_robot_description_candidates
from app.services.project_store import load_manifest, project_dir


def _load_validation(project_id: str) -> dict:
    path = project_dir(project_id) / "import_validation.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_launch_readiness(project_id: str) -> dict:
    pdir = project_dir(project_id)
    if not pdir.is_dir():
        return {
            "project_id": project_id,
            "can_launch_native": False,
            "can_launch_web": False,
            "can_preview_skeleton_web": False,
            "reasons": [f"Project not found: {project_id}"],
        }

    reasons: list[str] = []
    manifest = load_manifest(project_id)
    candidates = resolve_robot_description_candidates(manifest, pdir)
    validation = _load_validation(project_id)
    sim_ready = validation.get("simulation_readiness") or {}
    status = str(sim_ready.get("status") or "")
    has_joints = bool(sim_ready.get("joint"))
    mechanism_ok = status == "mechanism_imported" or has_joints

    if not candidates:
        reasons.append("No URDF or MJCF robot description found. Import a motion file first.")
    else:
        missing = [str(p) for _, p in candidates if not Path(p).is_file()]
        if missing:
            reasons.append(f"Robot description file missing on disk: {missing[0]}")

    missing_meshes = validation.get("geometry", {}).get("missing_mesh_references") or []
    mesh_table = validation.get("geometry", {}).get("mesh_table") or []
    missing_count = len(missing_meshes)

    genesis_ok = genesis_runtime.status().installed
    if not genesis_ok:
        reasons.append("Genesis is not installed. Run pip install genesis-world.")

    can_launch_native = (
        bool(candidates)
        and mechanism_ok
        and all(Path(p).is_file() for _, p in candidates)
        and missing_count == 0
    )
    can_launch_web = can_launch_native and genesis_ok
    can_preview_skeleton_web = bool(candidates) and mechanism_ok and genesis_ok and missing_count > 0

    disabled_reason_web: str | None = None
    disabled_reason_native: str | None = None

    if not can_launch_native:
        if missing_count > 0:
            disabled_reason_native = (
                f"Cannot launch: missing URDF mesh asset {missing_meshes[0]}. "
                "Upload the full mesh folder or a zip bundle."
            )
        else:
            disabled_reason_native = reasons[0] if reasons else "Launch not available"
    if not can_launch_web:
        if not genesis_ok:
            disabled_reason_web = "Genesis is not installed. Run pip install genesis-world."
        elif missing_count > 0:
            first_missing = str(missing_meshes[0])
            disabled_reason_web = (
                f"Cannot launch: missing URDF mesh asset {first_missing}. "
                "Upload the full mesh folder or a zip bundle."
            )
        else:
            disabled_reason_web = reasons[0] if reasons else "Launch not available"

    return {
        "project_id": project_id,
        "can_launch_native": can_launch_native,
        "can_launch_web": can_launch_web,
        "can_preview_skeleton_web": can_preview_skeleton_web,
        "missing_mesh_count": missing_count,
        "first_missing_mesh": str(missing_meshes[0]) if missing_meshes else None,
        "mesh_table": mesh_table[:20],
        "robot_description_candidates": [{"type": t, "path": str(p)} for t, p in candidates[:5]],
        "simulation_readiness": sim_ready,
        "reasons": reasons,
        "disabled_reason_native": disabled_reason_native,
        "disabled_reason_web": disabled_reason_web,
        "step_note": validation.get("geometry", {}).get(
            "step_note",
            "STEP is stored as an optional asset and does not replace missing URDF mesh files.",
        ),
        "launch_summary": validation.get("launch_summary") or {},
    }
