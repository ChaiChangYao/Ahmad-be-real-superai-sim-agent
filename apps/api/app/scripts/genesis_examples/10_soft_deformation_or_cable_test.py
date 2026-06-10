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


def main() -> None:
    # Placeholder rigid proxy until project wires soft material setup from Genesis FEM/MPM entities.
    runtime = GenesisNativeRuntime()
    scene = runtime.create_scene(GenesisRunConfig(show_viewer=False))
    add_plane(scene)
    deform_proxy = add_box(scene, pos=(0.0, 0.0, 0.8), size=(0.2, 0.2, 0.2), fixed=False)
    runtime.build_scene(scene)
    run = runtime.run_scene(scene, n_steps=180, tracked_entities={"target": deform_proxy})
    out = {
        "step_count": run["step_count"],
        "deformation_metric": None,
        "status": "warning",
        "warning": "Soft/cable deformation test currently uses rigid proxy. Not certified FEA.",
    }
    out_dir = Path("sim-data") / "runs" / "genesis_examples"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "10_soft_deformation_or_cable_test.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print({"output": str(out_path), "status": out["status"], "warning": out["warning"]})


if __name__ == "__main__":
    main()
