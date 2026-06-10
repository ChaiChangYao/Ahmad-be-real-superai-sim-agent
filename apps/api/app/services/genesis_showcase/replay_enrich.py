"""Ensure replay bundles expose raw frames, smooth preview, and motion diagnostics."""
from __future__ import annotations

from typing import Any

from app.services.genesis_showcase.replay_motion_diagnostics import analyze_replay_motion, choose_preview_mode, log_motion_diagnostics, should_generate_smooth_preview
from app.services.genesis_showcase.replay_smooth_preview import generate_dense_trim_preview, generate_smooth_preview, validate_smooth_preview, cap_preview_frames


def _infer_demo_type(meta: dict[str, Any], scene: dict[str, Any]) -> str:
    script_path = str(meta.get("script_path") or meta.get("script_relpath") or "").lower()
    scenario_id = str(meta.get("scenario_id") or "").lower()
    path_hint = f"{script_path} {scenario_id}"
    if "/sensors/" in script_path or "examples/sensors/" in script_path or "sensor-" in scenario_id:
        if any(token in path_hint for token in ("imu", "lidar", "contact", "tactile", "temperature")):
            return "telemetry"
        return "hybrid"
    explicit = str(meta.get("demo_type") or scene.get("demoType") or "").strip()
    if explicit in ("motion", "telemetry", "hybrid"):
        return explicit
    return "motion"


def _infer_catalog_kind(meta: dict[str, Any], scene: dict[str, Any]) -> str:
    explicit = str(meta.get("kind") or scene.get("kind") or "").strip()
    if explicit in ("simulation", "sensor", "gui"):
        return explicit
    demo_type = _infer_demo_type(meta, scene)
    if demo_type in ("telemetry", "hybrid"):
        return "sensor"
    return "simulation"


def _tracked_object_ids(objects: list[dict]) -> list[str]:
    return [
        str(o["id"])
        for o in objects
        if o.get("type") != "checker_floor" and not str(o.get("id", "")).startswith("env/")
    ]


def _preview_is_valid(preview_frames: list[dict], object_ids: list[str]) -> bool:
    if len(preview_frames) <= 1:
        return True
    validation = validate_smooth_preview(preview_frames, object_ids)
    return bool(validation.get("valid"))


def enrich_replay_bundle(data: dict[str, Any]) -> dict[str, Any]:
    frames = data.get("frames") if isinstance(data.get("frames"), list) else []
    raw_frames = data.get("raw_frames") if isinstance(data.get("raw_frames"), list) else frames
    preview_frames = data.get("preview_frames") if isinstance(data.get("preview_frames"), list) else []
    objects = data.get("objects") if isinstance(data.get("objects"), list) else []
    meta = dict(data.get("meta") or {})
    scene = dict(data.get("scene") or {})

    if not raw_frames:
        return data

    object_ids = _tracked_object_ids(objects)
    motion_diag = meta.get("motion_diagnostics")
    if not isinstance(motion_diag, dict):
        motion_diag = analyze_replay_motion(raw_frames, object_ids or None)
        log_motion_diagnostics(motion_diag)
        meta["motion_diagnostics"] = motion_diag
        meta["source_frame_count"] = len(raw_frames)
        meta["unique_pose_count"] = motion_diag.get("unique_pose_count")
        meta["longest_freeze_run"] = motion_diag.get("longest_freeze_run")
        meta["recorder_issue"] = motion_diag.get("recorder_issue")

    unique = int(motion_diag.get("unique_pose_count") or len(raw_frames))
    demo_type = _infer_demo_type(meta, scene)
    catalog_kind = _infer_catalog_kind(meta, scene)
    meta["kind"] = catalog_kind
    meta["demo_type"] = demo_type
    apply_visual_trim = catalog_kind == "simulation" and demo_type == "motion"
    needs_smooth = apply_visual_trim and should_generate_smooth_preview(motion_diag, len(raw_frames))
    preview_mode = choose_preview_mode(motion_diag, len(raw_frames)) if needs_smooth else "raw"
    preserve_holds = str(meta.get("preview_mode") or scene.get("previewMode") or "") == "preserve_holds"
    telemetry = data.get("telemetry") if isinstance(data.get("telemetry"), dict) else None
    telemetry_count = len((telemetry or {}).get("timestamps") or [])
    if telemetry_count:
        meta.setdefault("telemetry_sample_count", telemetry_count)
        meta.setdefault("demo_type", demo_type)

    if needs_smooth:
        if preview_frames and _preview_is_valid(preview_frames, object_ids):
            preview_meta = meta.get("preview_meta") if isinstance(meta.get("preview_meta"), dict) else {}
            meta.setdefault("preview_validation", preview_meta.get("validation"))
            meta.setdefault("preview_motion_diagnostics", preview_meta.get("preview_motion_diagnostics"))
        else:
            if preview_frames:
                print(
                    "[showcase_launcher] Stored smooth preview failed validation; regenerating full replay preview.",
                    flush=True,
                )
            preview_fps = float(scene.get("playback_fps") or meta.get("playback_fps") or 24)
            if preview_mode == "dense_trim":
                preview_frames, preview_meta = generate_dense_trim_preview(
                    raw_frames,
                    object_ids=object_ids or None,
                    preview_fps=preview_fps,
                )
            else:
                preview_frames, preview_meta = generate_smooth_preview(
                    raw_frames,
                    object_ids=object_ids or None,
                    preview_fps=preview_fps,
                    preserve_holds=preserve_holds,
                )
                preview_frames, cap_info = cap_preview_frames(
                    raw_frames,
                    preview_frames,
                    preview_fps=preview_fps,
                    object_ids=object_ids or None,
                    demo_kind=catalog_kind,
                )
                preview_meta["cap_info"] = cap_info
                meta["preview_expansion_ratio"] = cap_info.get("preview_expansion_ratio")
                meta["preview_duration_sec"] = cap_info.get("preview_duration_sec")
            print(
                f"[showcase_launcher] Preview ({preview_meta.get('mode')}, read-time): {len(raw_frames)} raw -> "
                f"{len(preview_frames)} preview frames",
                flush=True,
            )
            meta["preview_frame_count"] = len(preview_frames)
            meta["preview_meta"] = preview_meta
            meta["preview_validation"] = preview_meta.get("validation")
            meta["preview_motion_diagnostics"] = preview_meta.get("preview_motion_diagnostics")
            meta["replay_mode"] = preview_meta.get("mode") or ("preserve_holds" if preserve_holds else "smooth_preview")
            scene["sourceFrameCount"] = len(raw_frames)
            scene["uniquePoseCount"] = unique
            scene["previewFrameCount"] = len(preview_frames)
            scene["mode"] = meta["replay_mode"]

        playback_frames = preview_frames if not preserve_holds else raw_frames
    elif catalog_kind == "sensor" or demo_type in ("telemetry", "hybrid"):
        preview_frames = raw_frames
        playback_frames = raw_frames
        meta["preview_frame_count"] = len(raw_frames)
        meta["replay_mode"] = "raw"
        meta["visual_trim_applied"] = False
        meta["trim_reason"] = "telemetry_demo_preserve_samples"
        scene["sourceFrameCount"] = len(raw_frames)
        scene["previewFrameCount"] = len(raw_frames)
        scene["mode"] = "raw"
    elif preview_frames:
        playback_frames = preview_frames
        meta.setdefault("source_frame_count", len(raw_frames))
        meta.setdefault("preview_frame_count", len(preview_frames))
    else:
        preview_frames = raw_frames
        meta.setdefault("preview_frame_count", len(raw_frames))
        meta.setdefault("replay_mode", "raw")
        playback_frames = raw_frames

    meta.setdefault("source_frame_count", len(raw_frames))
    meta.setdefault("unique_pose_count", unique)
    meta.setdefault("preview_frame_count", len(preview_frames))
    meta.setdefault("demo_type", demo_type)
    if telemetry is not None:
        data["telemetry"] = telemetry

    data["frames"] = playback_frames
    data["raw_frames"] = raw_frames
    data["preview_frames"] = preview_frames
    data["meta"] = meta
    data["scene"] = scene
    return data
