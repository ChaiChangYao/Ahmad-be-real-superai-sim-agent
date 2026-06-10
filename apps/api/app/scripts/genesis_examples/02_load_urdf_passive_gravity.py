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
from app.services.genesis_native.metrics_extractor import extract_basic_metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--urdf", required=True)
    args = parser.parse_args()

    urdf_path = Path(args.urdf)
    if not urdf_path.exists():
        raise FileNotFoundError(f"URDF not found: {urdf_path}")

    runtime = GenesisNativeRuntime()
    scene = runtime.create_scene(GenesisRunConfig(show_viewer=False))
    add_plane(scene)
    robot = add_from_robot_description(scene, urdf_path, "urdf", fixed=False)
    runtime.build_scene(scene)
    run = runtime.run_scene(scene, n_steps=300, tracked_entities={"target": robot})
    metrics = extract_basic_metrics(robot, run["state_timeseries"])
    if metrics["fall_detected"]:
        metrics["failure_hints"] = [
            "base may be too narrow",
            "center of mass may be too high",
            "joint damping/limits may be missing",
            "collision geometry may be wrong",
        ]
    out_dir = Path("sim-data") / "runs" / "genesis_examples"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "02_load_urdf_passive_gravity.json"
    out_path.write_text(json.dumps({"run": run, "metrics": metrics, "urdf": str(urdf_path)}, indent=2), encoding="utf-8")
    print({"output": str(out_path), "metrics": metrics, "step_count": run["step_count"]})


if __name__ == "__main__":
    main()
