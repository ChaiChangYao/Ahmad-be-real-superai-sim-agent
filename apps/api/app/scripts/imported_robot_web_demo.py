"""Headless Genesis sim for imported robot projects (web replay recording)."""
from __future__ import annotations

import json
import os

import genesis as gs

from app.services.cad_import.urdf_generator import generate_urdf
from app.services.genesis.imported_robot_loader import load_imported_robot
from app.services.genesis_native.entity_loader import add_from_robot_description, add_plane
from app.services.project_store import load_manifest, project_dir


def _load_missing_meshes(project_id: str) -> list[str]:
    path = project_dir(project_id) / "import_validation.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("geometry", {}).get("missing_mesh_references") or [])
    except Exception:
        return []


def main() -> None:
    project_id = os.environ.get("BUILDABLES_PROJECT_ID")
    if not project_id:
        raise RuntimeError("BUILDABLES_PROJECT_ID environment variable is required")

    pdir = project_dir(project_id)
    manifest = load_manifest(project_id)
    skeleton_mode = os.environ.get("BUILDABLES_SKELETON_PREVIEW", "0") == "1"
    missing_meshes = _load_missing_meshes(project_id)
    steps = int(os.environ.get("BUILDABLES_CUSTOM_STEPS", "400"))

    if skeleton_mode:
        fallback_path = pdir / "generated" / "robot_description" / "genesis_physics.urdf"
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        generate_urdf(manifest, fallback_path)
        desc_type = "urdf"
        desc_path = str(fallback_path)
        print(
            f"[imported_robot_web_demo] Skeleton preview mode — {len(missing_meshes)} mesh file(s) missing; "
            "using generated mesh-free URDF.",
            flush=True,
        )
    else:
        if missing_meshes:
            first = missing_meshes[0]
            raise RuntimeError(
                f"Cannot launch: missing URDF mesh asset {first}. Upload the full mesh folder or a zip bundle."
            )
        info = load_imported_robot(pdir, manifest)
        desc_type = str(info["robot_description_type"])
        desc_path = info["robot_description_path"]

    print(f"[imported_robot_web_demo] project={project_id} desc={desc_path} steps={steps}", flush=True)

    gs.init(backend=gs.cpu)
    scene = gs.Scene(show_viewer=False, sim_options=gs.options.SimOptions(dt=0.01))
    add_plane(scene)
    add_from_robot_description(scene, desc_path, preferred_format=desc_type)
    scene.build()
    for i in range(steps):
        scene.step()
        if i % 100 == 0:
            print(f"[imported_robot_web_demo] step {i}/{steps}", flush=True)
    print("[imported_robot_web_demo] done", flush=True)


if __name__ == "__main__":
    main()
