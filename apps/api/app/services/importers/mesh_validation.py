"""Validate URDF mesh references at import time (before Genesis launch)."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from app.services.importers.asset_resolver import normalize_mesh_ref

SUPPORTED_MESH_EXTENSIONS = {".stl", ".obj", ".dae", ".glb", ".gltf", ".ply", ".fbx", ".mesh"}
UNSUPPORTED_EXTENSIONS = {".step", ".stp", ".iges", ".igs", ".brep"}


def _rel_to_imported(file_path: Path, imported_root: Path) -> str:
    try:
        return str(file_path.resolve().relative_to(imported_root.resolve())).replace("\\", "/")
    except ValueError:
        return file_path.name


def _usage_for_ref(ref: str, details: list[dict] | None) -> str:
    if not details:
        return "visual/collision"
    usages: set[str] = set()
    for row in details:
        if row.get("path") == ref or row.get("urdf_path") == ref:
            usages.add(str(row.get("usage") or "visual"))
    if len(usages) >= 2 or "both" in usages:
        return "both"
    if "collision" in usages:
        return "collision"
    if "visual" in usages:
        return "visual"
    return "visual/collision"


def _file_status(suffix: str, found: bool) -> str:
    if found:
        return "found"
    if suffix in UNSUPPORTED_EXTENSIONS:
        return "unsupported"
    if suffix and suffix not in SUPPORTED_MESH_EXTENSIONS:
        return "unsupported"
    return "missing"


def _action_needed(status: str, step_uploaded: bool) -> str:
    if status == "found":
        return ""
    if status == "auto_mapped":
        return "Auto-mapped by filename; verify mesh placement"
    if status == "unsupported":
        return "Convert to STL/OBJ/GLB or upload a supported mesh format"
    if step_uploaded:
        return "Upload mesh, zip bundle, or generate from STEP"
    return "Upload mesh file or zip bundle with meshes/ folder"


def validate_urdf_meshes(
    urdf_path: Path | None,
    mesh_refs: list[str],
    project_files: list[Path],
    *,
    mesh_ref_details: list[dict] | None = None,
    auto_map_basenames: bool = True,
) -> tuple[dict[str, str], list[str], list[dict], list[str]]:
    """Resolve mesh refs on disk, attempt basename auto-mapping, return table + logs."""
    auto_map_log: list[str] = []
    if urdf_path is None:
        table = [
            {
                "urdf_path": ref,
                "resolved_local_path": "",
                "usage": _usage_for_ref(ref, mesh_ref_details),
                "file_type": Path(normalize_mesh_ref(ref)).suffix.lower().lstrip(".") or "unknown",
                "status": "missing",
                "action_needed": "Upload URDF with mesh files",
            }
            for ref in dict.fromkeys(mesh_refs)
        ]
        return {}, list(dict.fromkeys(mesh_refs)), table, auto_map_log

    urdf_dir = urdf_path.parent
    imported_root = urdf_dir
    for parent in [urdf_dir, *urdf_dir.parents]:
        if parent.name == "imported":
            imported_root = parent
            break

    by_name = {p.name.lower(): p for p in project_files if p.is_file()}
    by_rel: dict[str, Path] = {}
    for path in project_files:
        if not path.is_file():
            continue
        by_rel[_rel_to_imported(path, imported_root).lower()] = path
        by_rel[str(path).replace("\\", "/").lower()] = path

    resolved: dict[str, str] = {}
    table: list[dict] = []
    seen: set[str] = set()

    unique_refs = list(dict.fromkeys(mesh_refs))
    for ref in unique_refs:
        if ref in seen:
            continue
        seen.add(ref)
        normalized = normalize_mesh_ref(ref)
        candidate = (urdf_dir / normalized).resolve()
        suffix = candidate.suffix.lower()
        usage = _usage_for_ref(ref, mesh_ref_details)
        found = candidate.is_file()
        status = _file_status(suffix, found)
        resolved_path = str(candidate)

        if not found and auto_map_basenames and status == "missing":
            key_name = Path(normalized).name.lower()
            key_rel = normalized.lower()
            source: Path | None = None
            if key_rel in by_rel and by_rel[key_rel].is_file():
                source = by_rel[key_rel]
            elif key_name in by_name and by_name[key_name].is_file():
                source = by_name[key_name]

            if source is not None and source.resolve() != candidate:
                candidate.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, candidate)
                auto_map_log.append(
                    f"Auto-mapped {source.name} → {normalized} (URDF expected path preserved)",
                )
                found = True
                status = "auto_mapped"
                resolved_path = str(candidate.resolve())

        entry = {
            "urdf_path": ref,
            "resolved_local_path": resolved_path,
            "usage": usage,
            "file_type": suffix.lstrip(".") or "unknown",
            "status": status,
            "action_needed": _action_needed(status, any(p.suffix.lower() in {".step", ".stp"} for p in project_files)),
        }
        table.append(entry)
        if found:
            resolved[ref] = resolved_path

    missing = [row["urdf_path"] for row in table if row["status"] in {"missing", "unsupported"}]
    return resolved, missing, table, auto_map_log
