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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mjcf", required=True)
    args = parser.parse_args()
    mjcf_path = Path(args.mjcf)
    if not mjcf_path.exists():
        raise FileNotFoundError(f"MJCF not found: {mjcf_path}")

    runtime = GenesisNativeRuntime()
    scene = runtime.create_scene(GenesisRunConfig(show_viewer=False))
    add_plane(scene)
    robot = add_from_robot_description(scene, mjcf_path, "mjcf", fixed=False)
    runtime.build_scene(scene)
    run = runtime.run_scene(scene, n_steps=240, tracked_entities={"target": robot})
    out_dir = Path("sim-data") / "runs" / "genesis_examples"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "03_load_mjcf_robot.json"
    out_path.write_text(json.dumps({"run": run, "mjcf": str(mjcf_path)}, indent=2), encoding="utf-8")
    print({"output": str(out_path), "step_count": run["step_count"]})


if __name__ == "__main__":
    main()
