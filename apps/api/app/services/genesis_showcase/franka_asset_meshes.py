"""Export Franka Panda link meshes from Genesis package OBJ assets (deterministic)."""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


MAX_TRIS_PER_LINK = 8000


def _find_franka_asset_root() -> Path | None:
    try:
        import genesis as gs

        pkg = Path(gs.__file__).resolve().parent
        candidate = pkg / "assets" / "xml" / "franka_emika_panda"
        if (candidate / "panda.xml").is_file():
            return candidate
    except Exception:
        pass
    return None


def _load_obj_mesh(obj_path: Path) -> tuple[list[list[float]], list[list[int]]]:
    verts: list[list[float]] = []
    faces: list[list[int]] = []
    for line in obj_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        if parts[0] == "v" and len(parts) >= 4:
            verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
        elif parts[0] == "f" and len(parts) >= 4:
            face = []
            for p in parts[1:4]:
                face.append(int(p.split("/")[0]) - 1)
            faces.append(face)
    return verts, faces


def _merge_meshes(meshes: list[tuple[list[list[float]], list[list[int]]]]) -> tuple[list[float], list[int]]:
    positions: list[float] = []
    indices: list[int] = []
    offset = 0
    for verts, faces in meshes:
        for v in verts:
            positions.extend(v)
        for f in faces:
            indices.extend([offset + i for i in f])
        offset += len(verts)
    return positions, indices


def _mesh_assets(asset_root: Path) -> dict[str, str]:
    """Map MJCF mesh reference name -> asset file path."""
    tree = ET.parse(asset_root / "panda.xml")
    root = tree.getroot()
    mesh_assets: dict[str, str] = {}
    for mesh in root.findall(".//asset/mesh"):
        file = mesh.get("file", "")
        if not file:
            continue
        name = mesh.get("name") or Path(file).stem
        mesh_assets[name] = file
    return mesh_assets


def _link_mesh_map(asset_root: Path) -> dict[str, list[str]]:
    """Map MJCF body name -> list of mesh asset files used by visual geoms."""
    mesh_assets = _mesh_assets(asset_root)

    tree = ET.parse(asset_root / "panda.xml")
    root = tree.getroot()
    link_meshes: dict[str, list[str]] = {}

    def walk_body(body: ET.Element) -> None:
        name = body.get("name")
        if name:
            refs: list[str] = []
            for geom in body.findall("geom"):
                geom_class = geom.get("class") or ""
                if geom_class != "visual" and geom.get("type") != "mesh":
                    continue
                if geom_class == "collision":
                    continue
                mesh_ref = geom.get("mesh")
                if mesh_ref and mesh_ref in mesh_assets:
                    refs.append(mesh_assets[mesh_ref])
            if refs:
                link_meshes[name] = refs
        for child in body.findall("body"):
            walk_body(child)

    for worldbody in root.findall("worldbody"):
        for body in worldbody.findall("body"):
            walk_body(body)
    return link_meshes


def export_franka_link_meshes(mesh_dir: Path) -> dict[str, str]:
    """
    Export per-link meshes from Genesis Franka OBJ assets.
    Returns map link_name -> relative meshPath (meshes/franka/linkN.json).
    """
    asset_root = _find_franka_asset_root()
    if asset_root is None:
        return {}

    assets_dir = asset_root / "assets"
    link_map = _link_mesh_map(asset_root)
    out_dir = mesh_dir / "franka"
    out_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, str] = {}

    for link_name, obj_files in link_map.items():
        meshes: list[tuple[list[list[float]], list[list[int]]]] = []
        for rel in obj_files:
            obj_path = assets_dir / Path(rel).name
            if not obj_path.is_file():
                obj_path = assets_dir / rel.replace("assets/", "")
            if not obj_path.is_file():
                obj_path = asset_root / rel
            if not obj_path.is_file():
                continue
            try:
                meshes.append(_load_obj_mesh(obj_path))
            except Exception:
                continue
        if not meshes:
            continue
        positions, indices = _merge_meshes(meshes)
        if len(indices) > MAX_TRIS_PER_LINK * 3:
            try:
                import numpy as np
                import trimesh

                tri = trimesh.Trimesh(
                    vertices=np.array(positions).reshape(-1, 3),
                    faces=np.array(indices).reshape(-1, 3),
                    process=False,
                )
                tri = tri.simplify_quadric_decimation(MAX_TRIS_PER_LINK)
                positions = tri.vertices.reshape(-1).tolist()
                indices = tri.faces.reshape(-1).tolist()
            except Exception:
                pass
        safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", link_name)
        rel_path = f"meshes/franka/{safe_name}.json"
        out_path = mesh_dir.parent / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps({"positions": positions, "indices": indices}), encoding="utf-8")
        result[link_name] = rel_path
    return result
