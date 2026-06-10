from __future__ import annotations

from pathlib import Path
import json


def write_render_stub(run_dir: Path, frames: list[dict] | None = None) -> dict:
    frames = frames or []
    out = {
        "render_backend": "genesis",
        "frame_count": len(frames),
        "frames": frames,
        "note": "Native Genesis render integration is environment-dependent. This artifact records render metadata for replay.",
    }
    out_path = run_dir / "render_output.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return {"render_output_path": str(out_path)}
