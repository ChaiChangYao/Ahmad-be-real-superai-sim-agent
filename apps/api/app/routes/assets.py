from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.cad_import.mesh_importer import import_mesh_asset
from app.services.cad_import.step_importer import import_step_source
from app.services.project_store import load_manifest, save_manifest, project_dir

router = APIRouter(tags=["assets"])

MESH_EXTS = {".stl", ".obj", ".glb", ".gltf"}


@router.post("/projects/{project_id}/assets/upload")
async def upload_asset(project_id: str, file: UploadFile = File(...)) -> dict:
    pdir = project_dir(project_id)
    if not pdir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    manifest = load_manifest(project_id)
    assets_dir = pdir / "assets"
    suffix = Path(file.filename or "").suffix.lower()
    data = await file.read()
    asset_id = f"asset-{uuid4().hex[:8]}"
    notes = None

    if suffix in MESH_EXTS:
        saved = import_mesh_asset(assets_dir, file.filename or f"{asset_id}{suffix}", data)
        asset_type = suffix.lstrip(".")
    elif suffix in {".step", ".stp"}:
        saved, notes = import_step_source(assets_dir, file.filename or f"{asset_id}.step", data)
        asset_type = "step"
    elif suffix == ".urdf":
        saved = import_mesh_asset(assets_dir, file.filename or f"{asset_id}.urdf", data)
        asset_type = "urdf"
    elif suffix == ".xml":
        saved = import_mesh_asset(assets_dir, file.filename or f"{asset_id}.xml", data)
        asset_type = "mjcf"
    else:
        saved = import_mesh_asset(assets_dir, file.filename or asset_id, data)
        asset_type = "other"

    manifest.assets.append(
        {
            "id": asset_id,
            "name": saved.stem,
            "type": asset_type,
            "file_path": str(saved),
            "original_filename": file.filename or saved.name,
            "unit_scale_to_meters": 1.0,
            "visual_only": asset_type in {"stl", "obj", "glb", "gltf"},
            "generated": False,
            "source_asset_id": None,
            "notes": notes,
        }
    )
    save_manifest(project_id, manifest)
    return {"asset_id": asset_id, "asset_type": asset_type, "path": str(saved), "notes": notes}


@router.get("/projects/{project_id}/assets")
def list_assets(project_id: str) -> list[dict]:
    manifest = load_manifest(project_id)
    return [a.model_dump() for a in manifest.assets]


@router.get("/projects/{project_id}/assets/{asset_id}")
def get_asset(project_id: str, asset_id: str) -> dict:
    manifest = load_manifest(project_id)
    for asset in manifest.assets:
        if asset.id == asset_id:
            return asset.model_dump()
    raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")


@router.delete("/projects/{project_id}/assets/{asset_id}")
def delete_asset(project_id: str, asset_id: str) -> dict:
    manifest = load_manifest(project_id)
    existing = [a for a in manifest.assets if a.id == asset_id]
    if not existing:
        raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")
    for asset in existing:
        p = Path(asset.file_path)
        if p.exists():
            p.unlink()
    manifest.assets = [a for a in manifest.assets if a.id != asset_id]
    save_manifest(project_id, manifest)
    return {"deleted": True, "asset_id": asset_id}
