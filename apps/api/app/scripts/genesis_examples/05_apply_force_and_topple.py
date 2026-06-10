from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.genesis_native.entity_loader import add_box, add_plane
from app.services.genesis_native.force_applier import apply_lateral_force
from app.services.genesis_native.genesis_runtime import GenesisNativeRuntime, GenesisRunConfig
from app.services.genesis_native.metrics_extractor import extract_basic_metrics


def main() -> None:
    runtime = GenesisNativeRuntime()
    scene = runtime.create_scene(GenesisRunConfig(show_viewer=False))
    add_plane(scene)
    box = add_box(scene, pos=(0.0, 0.0, 1.2), size=(0.15, 0.15, 0.8), fixed=False)
    runtime.build_scene(scene)
    applied = apply_lateral_force(box, (120.0, 0.0, 0.0))
    run = runtime.run_scene(scene, n_steps=240, tracked_entities={"target": box})
    metrics = extract_basic_metrics(box, run["state_timeseries"], applied_force_n=120.0 if applied else None)
    out = {"applied_force": applied, "metrics": metrics, "step_count": run["step_count"]}
    out_dir = Path("sim-data") / "runs" / "genesis_examples"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "05_apply_force_and_topple.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print({"output": str(out_path), "metrics": metrics})


if __name__ == "__main__":
    main()
