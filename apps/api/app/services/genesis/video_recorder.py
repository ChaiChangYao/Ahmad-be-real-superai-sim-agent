from __future__ import annotations

from pathlib import Path


def save_frames_placeholder(run_dir: Path) -> Path:
    frames_dir = run_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    return frames_dir
