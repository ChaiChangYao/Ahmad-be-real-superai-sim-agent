from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.models.manifest import BuildablesPhysicsManifest
from app.services.manifest_validator import validate_manifest
from app.services.project_store import load_manifest, save_manifest

router = APIRouter(tags=["manifests"])


@router.get("/projects/{project_id}/manifest")
def get_manifest(project_id: str) -> dict:
    try:
        manifest = load_manifest(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}") from exc
    return manifest.model_dump()


@router.put("/projects/{project_id}/manifest")
def put_manifest(project_id: str, payload: dict) -> dict:
    try:
        manifest = BuildablesPhysicsManifest.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    save_manifest(project_id, manifest)
    saved = load_manifest(project_id)
    return {"saved": True, "manifest": saved.model_dump()}


@router.post("/projects/{project_id}/manifest/validate")
def validate_manifest_endpoint(project_id: str) -> dict:
    try:
        manifest = load_manifest(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}") from exc
    return validate_manifest(manifest)
