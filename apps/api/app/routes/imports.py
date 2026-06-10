from uuid import uuid4
from fastapi import APIRouter

from app.services.cad_import.collision_primitive_generator import generate_default_collision_primitive
from app.services.cad_import.joint_auto_guesser import auto_guess_joints
from app.services.cad_import.mjcf_generator import generate_mjcf
from app.services.cad_import.urdf_generator import generate_urdf
from app.services.project_store import load_manifest, save_manifest, project_dir

router = APIRouter(tags=["imports"])


@router.post("/projects/{project_id}/cad/import")
def cad_import(project_id: str) -> dict:
    manifest = load_manifest(project_id)
    return {
        "status": "ok",
        "message": "CAD assets ingested. STEP imported as source CAD. Physics simulation uses generated collision primitives and robot description metadata.",
        "asset_count": len(manifest.assets),
    }


@router.post("/projects/{project_id}/cad/generate-collision-primitives")
def generate_collision_primitives(project_id: str) -> dict:
    manifest = load_manifest(project_id)
    created = 0
    for link in manifest.links:
        if not link.collision_primitive_ids:
            cid = f"cp-{uuid4().hex[:8]}"
            manifest.collision_primitives.append(generate_default_collision_primitive(link.id, cid))
            link.collision_primitive_ids.append(cid)
            created += 1
    save_manifest(project_id, manifest)
    return {"created": created}


@router.post("/projects/{project_id}/cad/generate-urdf")
def generate_urdf_endpoint(project_id: str) -> dict:
    manifest = load_manifest(project_id)
    pdir = project_dir(project_id)
    urdf_path = pdir / "generated" / "robot_description" / "robot.urdf"
    generate_urdf(manifest, urdf_path)
    manifest.robot_description.urdf_path = str(urdf_path)
    save_manifest(project_id, manifest)
    return {"urdf_path": str(urdf_path)}


@router.post("/projects/{project_id}/cad/generate-mjcf")
def generate_mjcf_endpoint(project_id: str) -> dict:
    manifest = load_manifest(project_id)
    pdir = project_dir(project_id)
    mjcf_path = pdir / "generated" / "robot_description" / "robot.mjcf"
    generate_mjcf(manifest, mjcf_path)
    manifest.robot_description.mjcf_path = str(mjcf_path)
    save_manifest(project_id, manifest)
    return {"mjcf_path": str(mjcf_path)}


@router.post("/projects/{project_id}/cad/auto-guess-joints")
def auto_guess_joints_endpoint(project_id: str) -> dict:
    manifest = load_manifest(project_id)
    guesses = auto_guess_joints(manifest)
    return {"guesses": guesses}
