"""Scan project asset folders and build typed inventory."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from uuid import uuid4

from app.services.agentic.schemas import AssetRole, AssetSource, AssetStatus, UploadedAsset
from app.services.project_store import project_dir

MESH_EXTENSIONS = {".stl", ".obj", ".dae", ".glb", ".gltf", ".ply", ".fbx", ".mesh"}
CAD_EXTENSIONS = {".step", ".stp", ".iges", ".igs", ".brep"}
ROBOT_DESC_EXTENSIONS = {".urdf", ".xacro", ".mjcf"}
TEXTURE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tga"}
USD_EXTENSIONS = {".usd", ".usda", ".usdc"}
SCAN_ROOTS = ("assets/imported", "assets", "generated/robot_description", "generated/collision", "generated/step_preview")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _infer_role(path: Path) -> AssetRole:
    ext = path.suffix.lower()
    name_lower = path.name.lower()
    if ext in ROBOT_DESC_EXTENSIONS or (ext == ".xml" and "robot" in name_lower):
        return "robot_description"
    if ext in MESH_EXTENSIONS:
        return "mesh"
    if ext in CAD_EXTENSIONS:
        return "cad"
    if ext in TEXTURE_EXTENSIONS or ext == ".mtl":
        return "texture"
    if ext == ".py" and any(k in name_lower for k in ("control", "controller", "demo")):
        return "control_script"
    if ext == ".json" and any(k in name_lower for k in ("manifest", "metadata", "config")):
        return "metadata"
    if ext in USD_EXTENSIONS:
        return "mesh"
    return "unknown"


def _inventory_path(project_id: str) -> Path:
    return project_dir(project_id) / "asset_inventory.json"


def _atomic_write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    for attempt in range(8):
        try:
            tmp.replace(path)
            return
        except OSError:
            if attempt >= 7:
                path.write_text(payload, encoding="utf-8")
                tmp.unlink(missing_ok=True)
                return
            time.sleep(0.05 * (attempt + 1))


def _walk_asset_dirs(root: Path) -> list[Path]:
    files: list[Path] = []
    if not root.is_dir():
        return files
    for path in sorted(root.rglob("*")):
        if path.is_file():
            files.append(path)
    return files


def scan_project_assets(project_id: str, *, persist: bool = True) -> list[UploadedAsset]:
    """Walk project folders, hash files, assign roles, persist inventory JSON."""
    root = project_dir(project_id)
    if not root.is_dir():
        return []

    seen_paths: set[str] = set()
    assets: list[UploadedAsset] = []

    for rel_root in SCAN_ROOTS:
        scan_path = root / rel_root
        for file_path in _walk_asset_dirs(scan_path):
            key = str(file_path.resolve())
            if key in seen_paths:
                continue
            seen_paths.add(key)

            try:
                rel = str(file_path.relative_to(root)).replace("\\", "/")
            except ValueError:
                rel = file_path.name

            ext = file_path.suffix.lower().lstrip(".")
            role = _infer_role(file_path)
            source: AssetSource = "generated" if rel.startswith("generated/") else "user_upload"

            try:
                size = file_path.stat().st_size
                digest = _sha256(file_path)
            except OSError:
                size = 0
                digest = ""

            assets.append(
                UploadedAsset(
                    id=f"asset-{uuid4().hex[:12]}",
                    project_id=project_id,
                    original_filename=file_path.name,
                    stored_path=str(file_path.resolve()),
                    relative_path=rel,
                    file_type=ext or "unknown",
                    size_bytes=size,
                    sha256=digest,
                    role=role,
                    source=source,
                    status="found",
                ),
            )

    if persist:
        inv_path = _inventory_path(project_id)
        inv_path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(inv_path, [a.model_dump() for a in assets])

    return assets


def load_asset_inventory(project_id: str) -> list[UploadedAsset]:
    """Load persisted inventory or scan if missing."""
    inv_path = _inventory_path(project_id)
    if inv_path.is_file():
        for attempt in range(8):
            try:
                raw = inv_path.read_text(encoding="utf-8").strip()
                if not raw:
                    return scan_project_assets(project_id, persist=False)
                data = json.loads(raw)
                return [UploadedAsset.model_validate(row) for row in data]
            except (json.JSONDecodeError, ValueError):
                return scan_project_assets(project_id, persist=False)
            except OSError:
                if attempt >= 7:
                    return scan_project_assets(project_id, persist=False)
                time.sleep(0.05 * (attempt + 1))
    return scan_project_assets(project_id)


def find_assets_by_role(assets: list[UploadedAsset], role: AssetRole) -> list[UploadedAsset]:
    return [a for a in assets if a.role == role]


def match_asset_by_path(assets: list[UploadedAsset], resolved_path: str) -> UploadedAsset | None:
    norm = resolved_path.replace("\\", "/").lower()
    for asset in assets:
        if asset.stored_path.replace("\\", "/").lower() == norm:
            return asset
        if asset.relative_path.replace("\\", "/").lower() in norm or norm.endswith(asset.relative_path.replace("\\", "/").lower()):
            return asset
    return None
