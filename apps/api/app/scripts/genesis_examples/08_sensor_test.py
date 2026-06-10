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
from app.services.genesis_native.sensor_reader import read_entity_sensors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--urdf", required=True)
    args = parser.parse_args()
    runtime = GenesisNativeRuntime()
    scene = runtime.create_scene(GenesisRunConfig(show_viewer=False))
    add_plane(scene)
    robot = add_from_robot_description(scene, Path(args.urdf), "urdf", fixed=False)
    runtime.build_scene(scene)
    _ = runtime.run_scene(scene, n_steps=120, tracked_entities={"target": robot})
    sensor = read_entity_sensors(robot)
    out = {"sensor_output": sensor, "source": "genesis_state"}
    out_dir = Path("sim-data") / "runs" / "genesis_examples"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "08_sensor_test.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print({"output": str(out_path), "keys": list(sensor.keys())})


if __name__ == "__main__":
    main()
