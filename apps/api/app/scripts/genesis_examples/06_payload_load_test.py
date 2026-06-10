from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.genesis_native.entity_loader import add_box, add_from_robot_description, add_plane
from app.services.genesis_native.genesis_runtime import GenesisNativeRuntime, GenesisRunConfig
from app.services.genesis_native.metrics_extractor import extract_basic_metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--urdf", required=True)
    parser.add_argument("--payload-mass-kg", type=float, default=8.0)
    args = parser.parse_args()

    runtime = GenesisNativeRuntime()
    scene = runtime.create_scene(GenesisRunConfig(show_viewer=False))
    add_plane(scene)
    robot = add_from_robot_description(scene, Path(args.urdf), "urdf", fixed=False)
    _payload = add_box(scene, pos=(0.0, 0.0, 1.0), size=(0.2, 0.2, max(0.05, 0.05 * args.payload_mass_kg)), fixed=False)
    runtime.build_scene(scene)
    run = runtime.run_scene(scene, n_steps=300, tracked_entities={"target": robot})
    metrics = extract_basic_metrics(robot, run["state_timeseries"])
    metrics["payload_mass_kg"] = args.payload_mass_kg
    out = {"metrics": metrics, "step_count": run["step_count"]}
    out_dir = Path("sim-data") / "runs" / "genesis_examples"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "06_payload_load_test.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print({"output": str(out_path), "metrics": metrics})


if __name__ == "__main__":
    main()
