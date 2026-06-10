from __future__ import annotations

import subprocess
from typing import Any


def nvidia_gpu_hint() -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return {"available": False, "detail": "nvidia-smi not available (Nyx/IPC GPU demos need NVIDIA GPU)"}
        line = proc.stdout.strip().splitlines()[0]
        parts = [p.strip() for p in line.split(",")]
        return {
            "available": True,
            "gpu_name": parts[0] if parts else line,
            "driver_version": parts[1] if len(parts) > 1 else None,
            "nyx_note": "Nyx requires CUDA 12.9+ and driver 575+ per genesis-nyx README",
        }
    except Exception:
        return {"available": False, "detail": "Could not detect NVIDIA GPU (non-Nyx demos still work on CPU)"}
