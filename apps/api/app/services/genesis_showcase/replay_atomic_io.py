"""Atomic replay bundle writes with manifest sidecar."""
from __future__ import annotations

import json
import os
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MANIFEST_NAME = "replay_manifest.json"
TIMESERIES_NAME = "state_timeseries.json"
PARTIAL_TIMESERIES_NAME = "state_timeseries.partial.json"


def manifest_path(out_dir: Path) -> Path:
    return out_dir / MANIFEST_NAME


def timeseries_path(out_dir: Path) -> Path:
    return out_dir / TIMESERIES_NAME


def partial_timeseries_path(out_dir: Path) -> Path:
    return out_dir / PARTIAL_TIMESERIES_NAME


def effective_timeseries_path(out_dir: Path, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest if manifest is not None else read_manifest(out_dir)
    if manifest and str(manifest.get("status") or "") == "recording":
        partial = partial_timeseries_path(out_dir)
        if partial.is_file():
            return partial
    final = timeseries_path(out_dir)
    if final.is_file():
        return final
    partial = partial_timeseries_path(out_dir)
    return partial if partial.is_file() else final


def read_manifest(out_dir: Path) -> dict[str, Any] | None:
    path = manifest_path(out_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _safe_unlink(path: Path, *, retries: int = 10) -> None:
    if not path.exists():
        return
    last_err: OSError | None = None
    for attempt in range(retries):
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError as exc:
            last_err = exc
            time.sleep(0.05 * (attempt + 1))
    if last_err is not None:
        print(
            f"[showcase_launcher] Warning: could not remove {path.name} ({last_err}); final replay is already written.",
            flush=True,
        )


def _atomic_replace(src: Path, dst: Path, *, retries: int = 10) -> None:
    last_err: OSError | None = None
    for attempt in range(retries):
        try:
            os.replace(src, dst)
            return
        except PermissionError as exc:
            last_err = exc
            time.sleep(0.05 * (attempt + 1))
    try:
        shutil.copy2(src, dst)
        src.unlink(missing_ok=True)
    except OSError as exc:
        if last_err is not None:
            raise last_err from exc
        raise


def write_replay_bundle(
    out_dir: Path,
    payload: dict[str, Any],
    *,
    partial: bool = False,
    fps: float = 24.0,
    up_axis: str = "Z",
    source_frame_count: int | None = None,
    preview_frame_count: int | None = None,
    unique_pose_count: int | None = None,
    replay_mode: str | None = None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    previous = read_manifest(out_dir) or {}
    version = int(previous.get("version") or 0) + 1
    now = datetime.now(UTC).isoformat()
    frame_count = len(payload.get("frames") or [])
    status = "recording" if partial else "complete"

    extra: dict[str, Any] = {}
    if source_frame_count is not None:
        extra["sourceFrameCount"] = source_frame_count
    if preview_frame_count is not None:
        extra["previewFrameCount"] = preview_frame_count
    if unique_pose_count is not None:
        extra["uniquePoseCount"] = unique_pose_count
    if replay_mode is not None:
        extra["replayMode"] = replay_mode

    if partial:
        target_path = partial_timeseries_path(out_dir)
        target_path.write_text(json.dumps(payload), encoding="utf-8")
        pending: dict[str, Any] = {
            "status": status,
            "frameCount": frame_count,
            "fps": fps,
            "upAxis": up_axis.upper(),
            "version": version,
            "ready": True,
            "partialPath": PARTIAL_TIMESERIES_NAME,
            "createdAt": previous.get("createdAt") or now,
            "updatedAt": now,
            **extra,
        }
        manifest_path(out_dir).write_text(json.dumps(pending, indent=2), encoding="utf-8")
        return pending

    final_path = timeseries_path(out_dir)
    tmp_path = final_path.with_name(f"{final_path.name}.v{version}.tmp")
    tmp_path.write_text(json.dumps(payload), encoding="utf-8")

    pending = {
        "status": status,
        "frameCount": frame_count,
        "fps": fps,
        "upAxis": up_axis.upper(),
        "version": version,
        "ready": False,
        "createdAt": previous.get("createdAt") or now,
        "updatedAt": now,
        **extra,
    }
    manifest_path(out_dir).write_text(json.dumps(pending, indent=2), encoding="utf-8")

    _atomic_replace(tmp_path, final_path)
    _safe_unlink(partial_timeseries_path(out_dir))

    final_manifest = {
        **pending,
        "ready": True,
        "updatedAt": datetime.now(UTC).isoformat(),
    }
    final_manifest.pop("partialPath", None)
    final_manifest["completedAt"] = final_manifest["updatedAt"]
    manifest_path(out_dir).write_text(json.dumps(final_manifest, indent=2), encoding="utf-8")
    return final_manifest
