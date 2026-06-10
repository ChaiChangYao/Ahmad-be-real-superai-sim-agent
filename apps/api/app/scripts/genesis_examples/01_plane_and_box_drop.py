from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.genesis_native.entity_loader import add_box, add_plane
from app.services.genesis_native.genesis_runtime import GenesisNativeRuntime, GenesisRunConfig
from app.services.genesis_native.metrics_extractor import extract_basic_metrics


def main() -> None:
    runtime = GenesisNativeRuntime()
    scene = runtime.create_scene(GenesisRunConfig(show_viewer=False))
    add_plane(scene)
    box = add_box(scene, pos=(0.0, 0.0, 1.0), size=(0.2, 0.2, 0.2), fixed=False)
    runtime.build_scene(scene)
    run = runtime.run_scene(scene, n_steps=240, tracked_entities={"target": box})
    metrics = extract_basic_metrics(box, run["state_timeseries"])
    out_dir = Path("sim-data") / "runs" / "genesis_examples"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "01_plane_and_box_drop.json"
    out_path.write_text(json.dumps({"run": run, "metrics": metrics}, indent=2), encoding="utf-8")
    print({"output": str(out_path), "metrics": metrics, "step_count": run["step_count"]})


if __name__ == "__main__":
    main()
