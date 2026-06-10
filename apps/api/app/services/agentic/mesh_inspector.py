"""Mesh validation using trimesh — no backend crash on malformed files."""
from __future__ import annotations

from pathlib import Path

from app.services.agentic.file_inventory import find_assets_by_role, load_asset_inventory
from app.services.agentic.schemas import MeshInspection

SUPPORTED_LOAD = {".stl", ".obj", ".glb", ".gltf", ".ply", ".dae"}


def _guess_units(bounds: list[float] | None) -> str:
    if not bounds or len(bounds) < 6:
        return "unknown"
    extents = [bounds[3] - bounds[0], bounds[4] - bounds[1], bounds[5] - bounds[2]]
    max_ext = max(extents) if extents else 0.0
    if max_ext < 0.001:
        return "likely_mm_or_small"
    if max_ext > 100.0:
        return "likely_large_or_wrong_scale"
    return "likely_meters"


def inspect_mesh(path: Path, *, asset_id: str = "") -> MeshInspection:
    """Validate a single mesh file."""
    result = MeshInspection(
        asset_id=asset_id,
        path=str(path),
        file_type=path.suffix.lower().lstrip(".") or "unknown",
    )

    if not path.is_file():
        result.errors.append(f"Mesh file not found: {path}")
        return result

    if path.suffix.lower() not in SUPPORTED_LOAD:
        result.warnings.append(f"Extension {path.suffix} may have limited trimesh support.")

    try:
        import trimesh
        import numpy as np

        loaded = trimesh.load(str(path), force="mesh", process=False)
        if isinstance(loaded, trimesh.Scene):
            meshes = [g for g in loaded.geometry.values() if isinstance(g, trimesh.Trimesh)]
            if not meshes:
                result.errors.append("Scene contains no loadable mesh geometry.")
                return result
            mesh = trimesh.util.concatenate(meshes)
        elif isinstance(loaded, trimesh.Trimesh):
            mesh = loaded
        else:
            result.errors.append(f"Unsupported mesh type: {type(loaded).__name__}")
            return result

        if mesh.vertices is None or len(mesh.vertices) == 0:
            result.errors.append("Mesh has no vertices (empty or invalid).")
            return result

        result.parsed = True
        result.vertex_count = int(len(mesh.vertices))
        result.face_count = int(len(mesh.faces)) if mesh.faces is not None else 0

        bounds = mesh.bounds
        if bounds is not None:
            flat = [float(x) for x in bounds.flatten().tolist()]
            result.bounds = flat
            result.units_guess = _guess_units(flat)
            if result.units_guess == "likely_mm_or_small":
                result.warnings.append("Mesh bounds are very small — check unit scale (mm vs m).")
            if result.units_guess == "likely_large_or_wrong_scale":
                result.warnings.append("Mesh bounds are very large — check unit scale.")

        try:
            result.watertight = bool(mesh.is_watertight)
            if not mesh.is_watertight:
                result.warnings.append("Mesh is not watertight.")
        except Exception:
            result.watertight = None

        try:
            if mesh.is_watertight and mesh.volume > 0:
                result.volume = float(mesh.volume)
        except Exception:
            pass

        try:
            com = mesh.center_mass
            if com is not None:
                result.center_mass = [float(x) for x in np.asarray(com).flatten().tolist()[:3]]
        except Exception:
            pass

        if result.face_count == 0:
            result.errors.append("Mesh has zero faces.")

    except Exception as exc:
        result.errors.append(f"Failed to load mesh: {exc}")

    return result


def inspect_project_meshes(project_id: str) -> list[MeshInspection]:
    """Inspect all mesh-role assets in project inventory."""
    assets = load_asset_inventory(project_id)
    mesh_assets = find_assets_by_role(assets, "mesh")
    results: list[MeshInspection] = []
    for asset in mesh_assets:
        results.append(inspect_mesh(Path(asset.stored_path), asset_id=asset.id))
    return results
