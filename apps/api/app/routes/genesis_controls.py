from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException

from app.services.project_store import load_manifest, project_dir

router = APIRouter(tags=["genesis-controls"])


class JointApplyRequest(BaseModel):
    targets: list[float] = Field(default_factory=list)
    steps: int = 60


@router.get("/projects/{project_id}/genesis/dofs")
def get_project_dofs(project_id: str) -> dict:
    from app.services.genesis_native.scenario_executor import list_project_dofs

    manifest = load_manifest(project_id)
    try:
        return list_project_dofs(project_dir(project_id), manifest)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/projects/{project_id}/genesis/joints/apply")
def apply_project_joint_targets(project_id: str, payload: JointApplyRequest) -> dict:
    manifest = load_manifest(project_id)
    if not payload.targets:
        raise HTTPException(status_code=400, detail="targets required")
    try:
        from app.services.genesis_native.scenario_executor import apply_joint_command

        result = apply_joint_command(project_dir(project_id), manifest, payload.targets, steps=payload.steps)
        result["project_id"] = project_id
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
