from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.genesis_native.entity_loader import add_from_robot_description, add_plane
from app.services.genesis_native.genesis_runtime import GenesisNativeRuntime, GenesisRunConfig
from app.services.genesis_native.joint_controller import apply_joint_targets, list_dofs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--urdf", required=True)
    args = parser.parse_args()
    urdf_path = Path(args.urdf)
    runtime = GenesisNativeRuntime()
    scene = runtime.create_scene(GenesisRunConfig(show_viewer=False))
    add_plane(scene)
    robot = add_from_robot_description(scene, urdf_path, "urdf", fixed=True)
    runtime.build_scene(scene)
    dof_info = list_dofs(robot)
    targets = [0.2] * max(0, dof_info["count"])
    applied = apply_joint_targets(robot, targets) if targets else False
    run = runtime.run_scene(scene, n_steps=180, tracked_entities={"target": robot})
    reached = []
    if dof_info["count"] and hasattr(robot, "get_dofs_position"):
        reached = robot.get_dofs_position().tolist()
    out = {"dofs": dof_info, "targets": targets, "reached": reached, "applied": applied, "step_count": run["step_count"]}
    out_dir = Path("sim-data") / "runs" / "genesis_examples"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "04_joint_slider_control.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print({"output": str(out_path), "dof_count": dof_info["count"], "applied": applied})


if __name__ == "__main__":
    main()
