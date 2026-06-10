from __future__ import annotations

from pathlib import Path
from app.models.manifest import BuildablesPhysicsManifest


def generate_mjcf(manifest: BuildablesPhysicsManifest, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f'<mujoco model="{manifest.project_id}">', "  <worldbody>"]
    for link in manifest.links:
        lines.append(f'    <body name="{link.id}"/>')
    lines.extend(["  </worldbody>", "</mujoco>"])
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
