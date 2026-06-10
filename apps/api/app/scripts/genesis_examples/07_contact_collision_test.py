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
    runtime = GenesisNativeRuntime()
    scene = runtime.create_scene(GenesisRunConfig(show_viewer=False))
    add_plane(scene)
    box_a = add_box(scene, pos=(0.0, 0.0, 0.6), size=(0.25, 0.25, 0.25), fixed=False)
    _box_b = add_box(scene, pos=(0.0, 0.0, 1.2), size=(0.25, 0.25, 0.25), fixed=False)
    runtime.build_scene(scene)
    run = runtime.run_scene(scene, n_steps=180, tracked_entities={"target": box_a})
    contact_count = 0
    if hasattr(box_a, "get_contacts"):
        try:
            contacts = box_a.get_contacts()
            contact_count = len(contacts) if contacts is not None else 0
        except Exception:
            contact_count = 0
    out = {
        "step_count": run["step_count"],
        "contact_count": contact_count,
        "metric_source": "genesis_state" if contact_count else "derived_from_genesis_state",
    }
    out_dir = Path("sim-data") / "runs" / "genesis_examples"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "07_contact_collision_test.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print({"output": str(out_path), **out})


if __name__ == "__main__":
    main()
