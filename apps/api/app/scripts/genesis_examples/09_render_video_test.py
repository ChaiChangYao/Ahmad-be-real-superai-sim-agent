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
from app.services.genesis_native.render_recorder import write_render_stub


def main() -> None:
    runtime = GenesisNativeRuntime()
    scene = runtime.create_scene(GenesisRunConfig(show_viewer=False))
    add_plane(scene)
    box = add_box(scene, pos=(0.0, 0.0, 1.0), size=(0.2, 0.2, 0.2), fixed=False)
    runtime.build_scene(scene)
    run = runtime.run_scene(scene, n_steps=120, tracked_entities={"target": box})
    out_dir = Path("sim-data") / "runs" / "genesis_examples"
    out_dir.mkdir(parents=True, exist_ok=True)
    render_meta = write_render_stub(out_dir, frames=run["state_timeseries"][:30])
    out_path = out_dir / "09_render_video_test.json"
    out_path.write_text(json.dumps({"step_count": run["step_count"], "render": render_meta}, indent=2), encoding="utf-8")
    print({"output": str(out_path), "render_output": render_meta})


if __name__ == "__main__":
    main()
