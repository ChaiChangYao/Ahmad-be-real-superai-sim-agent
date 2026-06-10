"""Generate smooth interpolated preview frames from raw replay keyframes."""
from __future__ import annotations

import copy
import math
from typing import Any

from app.services.genesis_showcase.replay_motion_diagnostics import (
    KEYFRAME_ANG_EPS,
    KEYFRAME_POS_EPS,
    _aggregate_delta,
    _frame_transforms,
    count_moving_frames,
    extract_meaningful_keyframe_indices,
    find_first_motion_index,
    find_frozen_runs,
    find_last_motion_index,
    frame_has_visual_motion,
    is_meaningfully_different,
)

# Perceptual motion thresholds (distinct from exact-duplicate checks).
VISUAL_POS_EPS = 0.001
VISUAL_ANG_EPS = 0.02

# Collapse interior hold runs longer than this (frames) to a single representative frame.
HOLD_COLLAPSE_THRESHOLD = 3

# Validation thresholds for smooth preview quality.
VALIDATE_MAX_FREEZE_RUN = 2
VALIDATE_MAX_POS_JUMP = 0.12
VALIDATE_MAX_ANG_JUMP = 0.35

MAX_PREVIEW_FRAME_RATIO = 2.0
MAX_PREVIEW_FRAMES_ABSOLUTE = 1200


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_vec3(a: list[float], b: list[float], t: float) -> list[float]:
    return [_lerp(float(a[i]), float(b[i]), t) for i in range(3)]


def _slerp_quat(a: list[float], b: list[float], t: float) -> list[float]:
    aw, ax, ay, az = (float(a[0]), float(a[1]), float(a[2]), float(a[3]))
    bw, bx, by, bz = (float(b[0]), float(b[1]), float(b[2]), float(b[3]))
    dot = aw * bw + ax * bx + ay * by + az * bz
    if dot < 0.0:
        bw, bx, by, bz = -bw, -bx, -by, -bz
        dot = -dot
    if dot > 0.9995:
        return [
            _lerp(aw, bw, t),
            _lerp(ax, bx, t),
            _lerp(ay, by, t),
            _lerp(az, bz, t),
        ]
    theta0 = math.acos(min(1.0, max(-1.0, dot)))
    sin_theta0 = math.sin(theta0)
    if abs(sin_theta0) < 1e-8:
        return [aw, ax, ay, az]
    theta = theta0 * t
    s0 = math.sin(theta0 - theta) / sin_theta0
    s1 = math.sin(theta) / sin_theta0
    return [
        s0 * aw + s1 * bw,
        s0 * ax + s1 * bx,
        s0 * ay + s1 * by,
        s0 * az + s1 * bz,
    ]


def _lerp_qpos(a: dict[str, list[float]], b: dict[str, list[float]], t: float) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    keys = set(a.keys()) | set(b.keys())
    for key in keys:
        va = a.get(key) or []
        vb = b.get(key) or []
        n = max(len(va), len(vb))
        if n == 0:
            continue
        row = []
        for i in range(n):
            fa = float(va[i]) if i < len(va) else float(vb[i])
            fb = float(vb[i]) if i < len(vb) else float(va[i])
            row.append(_lerp(fa, fb, t))
        out[key] = row
    return out


def _interpolate_transform(a: dict, b: dict, t: float) -> dict:
    pos_a = a.get("position") or [0.0, 0.0, 0.0]
    pos_b = b.get("position") or pos_a
    qa = a.get("quaternion") or a.get("rotation_quat") or [1.0, 0.0, 0.0, 0.0]
    qb = b.get("quaternion") or b.get("rotation_quat") or qa
    return {
        "position": _lerp_vec3(pos_a, pos_b, t),
        "quaternion": _slerp_quat(qa, qb, t),
    }


def _collect_object_ids(raw_frames: list[dict], preferred: list[str] | None = None) -> list[str]:
    ids: set[str] = set(preferred or [])
    for frame in raw_frames:
        ids.update(_frame_transforms(frame).keys())
    return sorted(ids)


def _frame_has_visual_motion(
    frame_a: dict,
    frame_b: dict,
    object_ids: list[str],
    *,
    pos_eps: float = VISUAL_POS_EPS,
    ang_eps: float = VISUAL_ANG_EPS,
) -> bool:
    return frame_has_visual_motion(frame_a, frame_b, object_ids, pos_eps=pos_eps, ang_eps=ang_eps)


def trim_static_head(
    preview_frames: list[dict],
    object_ids: list[str],
    *,
    pos_eps: float = VISUAL_POS_EPS,
    ang_eps: float = VISUAL_ANG_EPS,
) -> tuple[list[dict], dict[str, Any]]:
    if len(preview_frames) <= 1:
        return preview_frames, {"trimmed_head_frames": 0, "first_motion_index": 0}
    first_motion = find_first_motion_index(preview_frames, object_ids, pos_eps=pos_eps, ang_eps=ang_eps)
    if first_motion <= 0:
        return preview_frames, {"trimmed_head_frames": 0, "first_motion_index": 0}
    print(
        f"[showcase_launcher] Smooth preview has frozen head of {first_motion} frames; trimming.",
        flush=True,
    )
    return preview_frames[first_motion:], {
        "trimmed_head_frames": first_motion,
        "first_motion_index": first_motion,
    }


def trim_motion_range(
    frames: list[dict],
    object_ids: list[str],
    *,
    pos_eps: float = VISUAL_POS_EPS,
    ang_eps: float = VISUAL_ANG_EPS,
) -> tuple[list[dict], dict[str, Any]]:
    """Trim static prefix and suffix from a frame sequence."""
    if len(frames) <= 1:
        return copy.deepcopy(frames), {
            "frozen_head_length": 0,
            "frozen_tail_length": 0,
            "first_motion_index": 0,
            "last_motion_index": 0,
        }
    first = find_first_motion_index(frames, object_ids, pos_eps=pos_eps, ang_eps=ang_eps)
    last = find_last_motion_index(frames, object_ids, pos_eps=pos_eps, ang_eps=ang_eps)
    trimmed = copy.deepcopy(frames[first : last + 1])
    head_len = first
    tail_len = max(0, len(frames) - 1 - last)
    if head_len > 0:
        print(f"[showcase_launcher] Trimmed frozen head: {head_len} frames", flush=True)
    if tail_len > 0:
        print(f"[showcase_launcher] Trimmed frozen tail: {tail_len} frames", flush=True)
    return trimmed, {
        "frozen_head_length": head_len,
        "frozen_tail_length": tail_len,
        "first_motion_index": first,
        "last_motion_index": last,
    }


def collapse_long_frozen_runs(
    frames: list[dict],
    object_ids: list[str],
    *,
    threshold: int = HOLD_COLLAPSE_THRESHOLD,
    preserve_holds: bool = False,
) -> tuple[list[dict], dict[str, Any]]:
    """Collapse interior no-motion runs to a single representative frame."""
    if preserve_holds or len(frames) <= 2:
        return copy.deepcopy(frames), {"collapsed_frames": 0, "trim_log": []}

    runs = find_frozen_runs(frames, object_ids)
    if not runs:
        return copy.deepcopy(frames), {"collapsed_frames": 0, "trim_log": []}

    drop: set[int] = set()
    trim_log: list[str] = []
    for run in runs:
        if run["length"] <= threshold:
            continue
        for idx in range(run["start"] + 1, run["end"] + 1):
            drop.add(idx)
        trim_log.append(
            f"Collapsed frozen run frames {run['start']}-{run['end']} ({run['length']} frames -> 1 hold frame)"
        )

    if not drop:
        return copy.deepcopy(frames), {"collapsed_frames": 0, "trim_log": trim_log}

    out = [copy.deepcopy(frames[i]) for i in range(len(frames)) if i not in drop]
    print(
        f"[showcase_launcher] Collapsed {len(drop)} interior frozen frames across {len(trim_log)} hold run(s).",
        flush=True,
    )
    return out, {"collapsed_frames": len(drop), "trim_log": trim_log}


def _preview_distinct_pose_count(preview_frames: list[dict], object_ids: list[str]) -> int:
    from app.services.genesis_showcase.replay_motion_diagnostics import _visual_state_key

    keys: set[str] = set()
    for frame in preview_frames:
        keys.add(_visual_state_key(frame, object_ids))
    return len(keys)


def prepare_motion_preview_source(
    raw_frames: list[dict],
    object_ids: list[str],
    *,
    preserve_holds: bool = False,
) -> tuple[list[dict], dict[str, Any]]:
    """Head/tail trim and optional middle hold collapse before preview generation."""
    trim_log: list[str] = []
    working, range_info = trim_motion_range(raw_frames, object_ids)
    trim_log.extend(
        [
            f"Trimmed frozen head: {range_info.get('frozen_head_length', 0)} frames",
            f"Trimmed frozen tail: {range_info.get('frozen_tail_length', 0)} frames",
        ]
    )
    if not preserve_holds:
        working, collapse_info = collapse_long_frozen_runs(working, object_ids, preserve_holds=False)
        trim_log.extend(collapse_info.get("trim_log") or [])
        range_info["collapsed_frames"] = collapse_info.get("collapsed_frames", 0)
    return working, {**range_info, "trim_log": trim_log, "source_frame_count": len(raw_frames)}


def detect_pose_groups(
    raw_frames: list[dict],
    object_ids: list[str],
    keyframe_indices: list[int] | None = None,
) -> list[dict[str, int]]:
    if not raw_frames:
        return []
    keyframes = keyframe_indices or extract_meaningful_keyframe_indices(raw_frames, object_ids)
    groups: list[dict[str, int]] = []
    for i, start in enumerate(keyframes):
        end = keyframes[i + 1] - 1 if i + 1 < len(keyframes) else len(raw_frames) - 1
        groups.append({"start": start, "end": end, "keyframe_index": start})
    return groups


def _segment_frame_count(
    start_frame: dict,
    end_frame: dict,
    object_ids: list[str],
    *,
    preview_fps: float,
    min_segment_frames: int,
    max_segment_frames: int,
) -> int:
    delta = _aggregate_delta(start_frame, end_frame, object_ids)
    motion = delta["max_pos"] + delta["max_ang"]
    if motion <= VISUAL_POS_EPS + VISUAL_ANG_EPS:
        return 1
    if motion <= KEYFRAME_POS_EPS + KEYFRAME_ANG_EPS:
        return 1
    scaled = int(round(preview_fps * (0.75 + min(2.5, motion * 0.35))))
    return max(min_segment_frames, min(max_segment_frames, scaled))


def _interpolate_segment(
    start_frame: dict,
    end_frame: dict,
    object_ids: list[str],
    segment_frames: int,
    *,
    seg_index: int,
    start_idx: int,
    end_idx: int,
    include_start: bool,
) -> list[dict]:
    if segment_frames <= 1:
        frame = copy.deepcopy(end_frame if not include_start else start_frame)
        return [
            {
                "transforms": copy.deepcopy(_frame_transforms(frame)),
                "qpos": copy.deepcopy(frame.get("qpos") or {}),
                "preview_segment": seg_index,
                "preview_alpha": 0.0 if include_start else 1.0,
                "source_keyframes": [start_idx, end_idx],
            }
        ]

    out: list[dict] = []
    start_t = _frame_transforms(start_frame)
    end_t = _frame_transforms(end_frame)
    steps = max(2, segment_frames)
    start_step = 0 if include_start else 1
    for step in range(start_step, steps):
        t = step / (steps - 1) if steps > 1 else 1.0
        transforms: dict[str, dict] = {}
        for oid in object_ids:
            ta = start_t.get(oid)
            tb = end_t.get(oid)
            if ta and tb:
                transforms[oid] = _interpolate_transform(ta, tb, t)
            elif ta:
                transforms[oid] = copy.deepcopy(ta)
            elif tb:
                transforms[oid] = copy.deepcopy(tb)
        qpos = _lerp_qpos(start_frame.get("qpos") or {}, end_frame.get("qpos") or {}, t)
        out.append(
            {
                "transforms": transforms,
                "qpos": qpos,
                "preview_segment": seg_index,
                "preview_alpha": round(t, 4),
                "source_keyframes": [start_idx, end_idx],
            }
        )
    return out


def _stamp_preview_timing(preview: list[dict], preview_fps: float) -> None:
    dt = 1.0 / max(1.0, preview_fps)
    for i, frame in enumerate(preview):
        frame["t"] = round(i * dt, 6)
        frame["step"] = i


def trim_static_tail(
    preview_frames: list[dict],
    object_ids: list[str],
    *,
    pos_eps: float = VISUAL_POS_EPS,
    ang_eps: float = VISUAL_ANG_EPS,
) -> tuple[list[dict], dict[str, Any]]:
    if len(preview_frames) <= 1:
        return preview_frames, {"trimmed_tail_frames": 0, "last_motion_index": 0}

    last_motion = 0
    for i in range(1, len(preview_frames)):
        if _frame_has_visual_motion(preview_frames[i - 1], preview_frames[i], object_ids, pos_eps=pos_eps, ang_eps=ang_eps):
            last_motion = i

    trimmed = len(preview_frames) - 1 - last_motion
    if trimmed <= 0:
        return preview_frames, {"trimmed_tail_frames": 0, "last_motion_index": last_motion}

    print(
        f"[showcase_launcher] Smooth preview still contains frozen run of {trimmed} frames; trimming required.",
        flush=True,
    )
    return preview_frames[: last_motion + 1], {
        "trimmed_tail_frames": trimmed,
        "last_motion_index": last_motion,
    }


def diagnose_preview_motion(
    preview_frames: list[dict],
    object_ids: list[str],
    *,
    pos_eps: float = VISUAL_POS_EPS,
    ang_eps: float = VISUAL_ANG_EPS,
) -> dict[str, Any]:
    if len(preview_frames) <= 1:
        return {
            "preview_frames": len(preview_frames),
            "moving_frames": len(preview_frames),
            "frozen_tail_starts_at": None,
            "longest_frozen_run": len(preview_frames),
            "max_position_jump": 0.0,
            "max_angular_jump_deg": 0.0,
            "visible_links_changing_after_tail": False,
        }

    moving_frames = 1
    longest_frozen = 1
    current_frozen = 1
    frozen_tail_starts_at: int | None = None
    max_pos_jump = 0.0
    max_ang_jump = 0.0

    for i in range(1, len(preview_frames)):
        delta = _aggregate_delta(preview_frames[i - 1], preview_frames[i], object_ids)
        has_motion = delta["max_pos"] > pos_eps or delta["max_ang"] > ang_eps
        max_pos_jump = max(max_pos_jump, delta["max_pos"])
        max_ang_jump = max(max_ang_jump, delta["max_ang"])
        if has_motion:
            moving_frames += 1
            current_frozen = 1
        else:
            current_frozen += 1
            longest_frozen = max(longest_frozen, current_frozen)

    for i in range(len(preview_frames) - 1, 0, -1):
        delta = _aggregate_delta(preview_frames[i - 1], preview_frames[i], object_ids)
        if delta["max_pos"] > pos_eps or delta["max_ang"] > ang_eps:
            if i + 1 < len(preview_frames):
                frozen_tail_starts_at = i + 1
            break

    tail_links_changing = False
    if frozen_tail_starts_at is not None and frozen_tail_starts_at < len(preview_frames) - 1:
        tail_links_changing = False
    else:
        tail_links_changing = moving_frames > len(preview_frames) * 0.5

    return {
        "preview_frames": len(preview_frames),
        "moving_frames": moving_frames,
        "frozen_tail_starts_at": frozen_tail_starts_at,
        "longest_frozen_run": longest_frozen,
        "max_position_jump": round(max_pos_jump, 6),
        "max_angular_jump_deg": round(math.degrees(max_ang_jump), 3),
        "visible_links_changing_after_tail": tail_links_changing,
    }


def validate_smooth_preview(
    preview_frames: list[dict],
    object_ids: list[str],
    motion_diag: dict[str, Any] | None = None,
) -> dict[str, Any]:
    motion_diag = motion_diag or diagnose_preview_motion(preview_frames, object_ids)

    if len(preview_frames) <= 1:
        return {
            **motion_diag,
            "repeated_consecutive_frames": 0,
            "valid": len(preview_frames) <= 1,
        }

    repeated = motion_diag["preview_frames"] - motion_diag["moving_frames"]
    valid = (
        motion_diag.get("frozen_tail_starts_at") is None
        and motion_diag.get("longest_frozen_run", 999) <= VALIDATE_MAX_FREEZE_RUN
        and motion_diag.get("max_position_jump", 999) <= VALIDATE_MAX_POS_JUMP
        and math.radians(motion_diag.get("max_angular_jump_deg", 999)) <= VALIDATE_MAX_ANG_JUMP
    )
    return {
        **motion_diag,
        "total_frames": motion_diag["preview_frames"],
        "repeated_consecutive_frames": repeated,
        "max_angular_jump_rad": round(math.radians(motion_diag.get("max_angular_jump_deg", 0.0)), 6),
        "valid": valid,
    }


def log_smooth_preview_plan(
    raw_frames: list[dict],
    keyframe_indices: list[int],
    pose_groups: list[dict[str, int]],
    segment_plan: list[dict[str, Any]],
    preview_frames: list[dict],
    validation: dict[str, Any],
    trim_info: dict[str, Any],
) -> None:
    print(
        f"[showcase_launcher] Raw replay: {len(raw_frames)} frames · "
        f"Distinct keyframes detected: {len(keyframe_indices)}",
        flush=True,
    )
    if trim_info.get("frozen_head_length"):
        print(
            f"[showcase_launcher] Trimmed frozen head: {trim_info.get('frozen_head_length')} frames",
            flush=True,
        )
    if trim_info.get("frozen_tail_length"):
        print(
            f"[showcase_launcher] Trimmed frozen tail: {trim_info.get('frozen_tail_length')} frames",
            flush=True,
        )
    if trim_info.get("collapsed_frames"):
        print(
            f"[showcase_launcher] Collapsed interior frozen frames: {trim_info.get('collapsed_frames')}",
            flush=True,
        )
    for line in trim_info.get("trim_log") or []:
        print(f"[showcase_launcher] {line}", flush=True)
    for i, group in enumerate(pose_groups):
        label = chr(ord("A") + i) if i < 26 else str(i)
        print(
            f"[showcase_launcher] Pose group {label}: frames {group['start']}-{group['end']}",
            flush=True,
        )
    for seg in segment_plan:
        print(
            f"[showcase_launcher] Smooth segment {seg['index']}: "
            f"raw {seg['start_idx']}->{seg['end_idx']} · {seg['segment_frames']} preview frames",
            flush=True,
        )
    print(
        f"[showcase_launcher] Smooth preview: total {len(preview_frames)} frames "
        f"(raw {len(raw_frames)}, trimmed_tail={trim_info.get('trimmed_tail_frames', 0)})",
        flush=True,
    )
    tail_at = validation.get("frozen_tail_starts_at")
    print(
        f"[showcase_launcher] Smooth preview diagnostics: preview frames={validation.get('preview_frames')} "
        f"moving frames={validation.get('moving_frames')} "
        f"distinct poses={trim_info.get('preview_distinct_pose_count', validation.get('preview_frames'))} "
        f"frozen tail starts at frame={tail_at if tail_at is not None else 'none'} "
        f"longest frozen run={validation.get('longest_frozen_run')} "
        f"max jump={validation.get('max_position_jump')} "
        f"links changing after tail={validation.get('visible_links_changing_after_tail')} "
        f"valid={validation.get('valid')}",
        flush=True,
    )


def cap_preview_frames(
    raw_frames: list[dict],
    preview_frames: list[dict],
    *,
    preview_fps: float = 24.0,
    object_ids: list[str] | None = None,
    demo_kind: str = "simulation",
) -> tuple[list[dict], dict[str, Any]]:
    """Fall back to dense trim when smooth preview expands beyond safe limits."""
    raw_count = len(raw_frames)
    preview_count = len(preview_frames)
    if raw_count <= 1 or preview_count <= raw_count:
        return preview_frames, {"capped": False, "preview_expansion_ratio": 1.0}

    ratio = preview_count / max(raw_count, 1)
    duration_cap = int(preview_fps * 50 * MAX_PREVIEW_FRAME_RATIO)
    max_allowed = min(
        MAX_PREVIEW_FRAMES_ABSOLUTE,
        max(int(raw_count * MAX_PREVIEW_FRAME_RATIO), duration_cap),
    )
    if preview_count <= max_allowed:
        preview_duration = preview_frames[-1].get("t", 0.0) if preview_frames else 0.0
        return preview_frames, {
            "capped": False,
            "preview_expansion_ratio": round(ratio, 3),
            "preview_duration_sec": round(float(preview_duration), 3),
            "demo_kind": demo_kind,
        }

    print(
        f"[showcase_launcher] Preview cap triggered: {preview_count} preview frames "
        f"exceeds max {max_allowed} (raw={raw_count}, ratio={ratio:.2f}, kind={demo_kind}); "
        "falling back to dense_trim.",
        flush=True,
    )
    capped, meta = generate_dense_trim_preview(
        raw_frames,
        object_ids=object_ids,
        preview_fps=preview_fps,
    )
    capped_duration = capped[-1].get("t", 0.0) if capped else 0.0
    cap_info = {
        "capped": True,
        "preview_expansion_ratio": round(len(capped) / max(raw_count, 1), 3),
        "preview_duration_sec": round(float(capped_duration), 3),
        "demo_kind": demo_kind,
        "cap_reason": "expansion_limit",
        "original_preview_count": preview_count,
        "capped_preview_count": len(capped),
    }
    meta["cap_info"] = cap_info
    return capped, cap_info


def generate_dense_trim_preview(
    raw_frames: list[dict],
    *,
    object_ids: list[str] | None = None,
    preview_fps: float = 24.0,
) -> tuple[list[dict], dict[str, Any]]:
    """Keep dense per-step motion (e.g. finger closing) and only trim static ends."""
    if len(raw_frames) <= 1:
        copied = copy.deepcopy(raw_frames)
        motion = diagnose_preview_motion(copied, object_ids or [])
        validation = validate_smooth_preview(copied, object_ids or [], motion)
        return copied, {
            "preview_frame_count": len(copied),
            "keyframe_count": len(copied),
            "mode": "dense_trim",
            "validation": validation,
        }

    ids = _collect_object_ids(raw_frames, object_ids)
    working_raw, prep_info = prepare_motion_preview_source(raw_frames, ids, preserve_holds=False)
    preview, tail_info = trim_static_tail(working_raw, ids)
    trim_info = {**prep_info, **tail_info}
    _stamp_preview_timing(preview, preview_fps)

    motion_diag = diagnose_preview_motion(preview, ids)
    validation = validate_smooth_preview(preview, ids, motion_diag)
    trim_info["preview_distinct_pose_count"] = _preview_distinct_pose_count(preview, ids)
    trim_info["moving_frame_count"] = count_moving_frames(preview, ids)
    print(
        f"[showcase_launcher] Dense trim preview: {len(raw_frames)} raw -> {len(preview)} preview frames "
        f"(head={prep_info.get('frozen_head_length', 0)}, tail={prep_info.get('frozen_tail_length', 0)}, "
        f"collapsed={prep_info.get('collapsed_frames', 0)}, moving={trim_info['moving_frame_count']})",
        flush=True,
    )

    return preview, {
        "preview_frame_count": len(preview),
        "keyframe_count": len(preview),
        "preview_fps": preview_fps,
        "mode": "dense_trim",
        "trim_info": trim_info,
        "validation": validation,
        "preview_motion_diagnostics": motion_diag,
    }


def generate_smooth_preview(
    raw_frames: list[dict],
    *,
    object_ids: list[str] | None = None,
    preview_fps: float = 24.0,
    min_segment_frames: int = 24,
    max_segment_frames: int = 60,
    preserve_holds: bool = False,
) -> tuple[list[dict], dict[str, Any]]:
    if len(raw_frames) <= 1:
        copied = copy.deepcopy(raw_frames)
        motion = diagnose_preview_motion(copied, object_ids or [])
        validation = validate_smooth_preview(copied, object_ids or [], motion)
        return copied, {
            "preview_frame_count": len(copied),
            "keyframe_count": len(copied),
            "mode": "raw",
            "validation": validation,
        }

    if preserve_holds:
        copied = copy.deepcopy(raw_frames)
        ids = _collect_object_ids(copied, object_ids)
        motion = diagnose_preview_motion(copied, ids)
        validation = validate_smooth_preview(copied, ids, motion)
        return copied, {
            "preview_frame_count": len(copied),
            "keyframe_count": len(copied),
            "mode": "preserve_holds",
            "validation": validation,
        }

    ids = _collect_object_ids(raw_frames, object_ids)
    working_raw, prep_info = prepare_motion_preview_source(raw_frames, ids, preserve_holds=False)

    keyframes = extract_meaningful_keyframe_indices(working_raw, ids)
    if len(keyframes) < 2:
        keyframes = [0, len(working_raw) - 1] if len(working_raw) > 1 else [0]

    pose_groups = detect_pose_groups(working_raw, ids, keyframes)

    preview: list[dict] = []
    segment_plan: list[dict[str, Any]] = []

    for seg in range(len(keyframes) - 1):
        start_idx = keyframes[seg]
        end_idx = keyframes[seg + 1]
        start_frame = working_raw[start_idx]
        end_frame = working_raw[end_idx]
        segment_frames = _segment_frame_count(
            start_frame,
            end_frame,
            ids,
            preview_fps=preview_fps,
            min_segment_frames=min_segment_frames,
            max_segment_frames=max_segment_frames,
        )
        # Skip zero-motion middle holds entirely; keep boundary keyframes via adjacent segments.
        if segment_frames <= 1 and seg > 0 and seg < len(keyframes) - 2:
            continue
        if segment_frames <= 1 and seg > 0:
            segment_frames = 1
        segment_plan.append(
            {
                "index": seg,
                "start_idx": start_idx,
                "end_idx": end_idx,
                "segment_frames": segment_frames,
            }
        )
        segment = _interpolate_segment(
            start_frame,
            end_frame,
            ids,
            segment_frames,
            seg_index=seg,
            start_idx=start_idx,
            end_idx=end_idx,
            include_start=seg == 0,
        )
        preview.extend(segment)

    if not preview:
        preview = copy.deepcopy(working_raw)
    else:
        _stamp_preview_timing(preview, preview_fps)

    trim_info: dict[str, Any] = dict(prep_info)
    preview, head_info = trim_static_head(preview, ids)
    trim_info.update(head_info)
    preview, tail_info = trim_static_tail(preview, ids)
    trim_info.update(tail_info)
    _stamp_preview_timing(preview, preview_fps)

    motion_diag = diagnose_preview_motion(preview, ids)
    validation = validate_smooth_preview(preview, ids, motion_diag)
    trim_info["preview_distinct_pose_count"] = _preview_distinct_pose_count(preview, ids)
    trim_info["moving_frame_count"] = count_moving_frames(preview, ids)
    log_smooth_preview_plan(working_raw, keyframes, pose_groups, segment_plan, preview, validation, trim_info)

    meta = {
        "preview_frame_count": len(preview),
        "keyframe_count": len(keyframes),
        "keyframes": keyframes,
        "pose_groups": pose_groups,
        "segment_plan": segment_plan,
        "preview_fps": preview_fps,
        "mode": "smooth_preview",
        "preserve_holds": preserve_holds,
        "trim_info": trim_info,
        "validation": validation,
        "preview_motion_diagnostics": motion_diag,
    }
    return preview, meta
