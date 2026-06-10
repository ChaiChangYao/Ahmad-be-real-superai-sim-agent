"""Analyze replay frame motion uniqueness and consecutive-frame deltas."""
from __future__ import annotations

import json
import math
from typing import Any


def _pos_delta(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b or len(a) < 3 or len(b) < 3:
        return 0.0
    return math.sqrt(sum((float(b[i]) - float(a[i])) ** 2 for i in range(3)))


def _quat_angle_delta(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b or len(a) < 4 or len(b) < 4:
        return 0.0
    aw, ax, ay, az = (float(a[0]), float(a[1]), float(a[2]), float(a[3]))
    bw, bx, by, bz = (float(b[0]), float(b[1]), float(b[2]), float(b[3]))
    dot = abs(aw * bw + ax * bx + ay * by + az * bz)
    dot = min(1.0, max(-1.0, dot))
    return 2.0 * math.acos(dot)


def _frame_transforms(frame: dict) -> dict[str, dict]:
    transforms = frame.get("transforms")
    if isinstance(transforms, dict):
        return transforms
    entities = frame.get("entities")
    if isinstance(entities, dict):
        return entities
    return {}


def _visual_state_key(frame: dict, object_ids: list[str]) -> str:
    payload: dict[str, Any] = {}
    transforms = _frame_transforms(frame)
    for oid in object_ids:
        t = transforms.get(oid)
        if not t:
            continue
        payload[oid] = {
            "p": t.get("position"),
            "q": t.get("quaternion") or t.get("rotation_quat"),
        }
    return json.dumps(payload, sort_keys=True)


def _aggregate_delta(prev: dict, cur: dict, object_ids: list[str]) -> dict[str, float]:
    prev_t = _frame_transforms(prev)
    cur_t = _frame_transforms(cur)
    max_pos = 0.0
    max_ang = 0.0
    per_object: dict[str, float] = {}
    for oid in object_ids:
        pt = prev_t.get(oid) or {}
        ct = cur_t.get(oid) or {}
        pd = _pos_delta(pt.get("position"), ct.get("position"))
        ad = _quat_angle_delta(pt.get("quaternion") or pt.get("rotation_quat"), ct.get("quaternion") or ct.get("rotation_quat"))
        combined = pd + ad
        per_object[oid] = combined
        max_pos = max(max_pos, pd)
        max_ang = max(max_ang, ad)
    return {"max_pos": max_pos, "max_ang": max_ang, "per_object": per_object}


KEYFRAME_POS_EPS = 0.01
KEYFRAME_ANG_EPS = 0.05


def is_meaningfully_different(
    frame_a: dict,
    frame_b: dict,
    object_ids: list[str],
    *,
    pos_eps: float = KEYFRAME_POS_EPS,
    ang_eps: float = KEYFRAME_ANG_EPS,
) -> bool:
    delta = _aggregate_delta(frame_a, frame_b, object_ids)
    return delta["max_pos"] > pos_eps or delta["max_ang"] > ang_eps


def extract_meaningful_keyframe_indices(
    frames: list[dict],
    object_ids: list[str],
    *,
    pos_eps: float = KEYFRAME_POS_EPS,
    ang_eps: float = KEYFRAME_ANG_EPS,
) -> list[int]:
    if not frames:
        return []
    indices = [0]
    for i in range(1, len(frames)):
        if is_meaningfully_different(frames[indices[-1]], frames[i], object_ids, pos_eps=pos_eps, ang_eps=ang_eps):
            indices.append(i)
    if indices[-1] != len(frames) - 1:
        if is_meaningfully_different(frames[indices[-1]], frames[-1], object_ids, pos_eps=pos_eps, ang_eps=ang_eps):
            indices.append(len(frames) - 1)
    return indices


def find_first_motion_index(
    frames: list[dict],
    object_ids: list[str],
    *,
    pos_eps: float = 0.001,
    ang_eps: float = 0.02,
) -> int:
    if not frames:
        return 0
    for i in range(1, len(frames)):
        delta = _aggregate_delta(frames[i - 1], frames[i], object_ids)
        if delta["max_pos"] > pos_eps or delta["max_ang"] > ang_eps:
            return i
    return 0


def find_last_motion_index(
    frames: list[dict],
    object_ids: list[str],
    *,
    pos_eps: float = 0.001,
    ang_eps: float = 0.02,
) -> int:
    if not frames:
        return 0
    last_motion = 0
    for i in range(1, len(frames)):
        delta = _aggregate_delta(frames[i - 1], frames[i], object_ids)
        if delta["max_pos"] > pos_eps or delta["max_ang"] > ang_eps:
            last_motion = i
    return last_motion


def frame_has_visual_motion(
    frame_a: dict,
    frame_b: dict,
    object_ids: list[str],
    *,
    pos_eps: float = 0.001,
    ang_eps: float = 0.02,
) -> bool:
    delta = _aggregate_delta(frame_a, frame_b, object_ids)
    return delta["max_pos"] > pos_eps or delta["max_ang"] > ang_eps


def find_frozen_runs(
    frames: list[dict],
    object_ids: list[str],
    *,
    pos_eps: float = 0.001,
    ang_eps: float = 0.02,
) -> list[dict[str, int]]:
    """Find consecutive frame ranges with no perceptual motion between pairs."""
    if len(frames) <= 1:
        return []
    runs: list[dict[str, int]] = []
    run_start: int | None = None
    for i in range(1, len(frames)):
        moving = frame_has_visual_motion(frames[i - 1], frames[i], object_ids, pos_eps=pos_eps, ang_eps=ang_eps)
        if not moving:
            if run_start is None:
                run_start = i - 1
        elif run_start is not None:
            runs.append({"start": run_start, "end": i - 1, "length": i - run_start})
            run_start = None
    if run_start is not None:
        runs.append({"start": run_start, "end": len(frames) - 1, "length": len(frames) - run_start})
    return runs


def count_moving_frames(
    frames: list[dict],
    object_ids: list[str],
    *,
    pos_eps: float = 0.001,
    ang_eps: float = 0.02,
) -> int:
    if len(frames) <= 1:
        return len(frames)
    moving = 1
    for i in range(1, len(frames)):
        if frame_has_visual_motion(frames[i - 1], frames[i], object_ids, pos_eps=pos_eps, ang_eps=ang_eps):
            moving += 1
    return moving


def analyze_replay_motion(frames: list[dict], object_ids: list[str] | None = None) -> dict[str, Any]:
    if not frames:
        return {
            "total_frames": 0,
            "unique_pose_count": 0,
            "longest_freeze_run": 0,
            "jump_frames": [],
            "top_moving_objects": [],
            "recorder_issue": "empty_replay",
        }

    if object_ids is None:
        object_ids = sorted(_frame_transforms(frames[0]).keys())

    motion_ids = [oid for oid in object_ids if any(_frame_transforms(f).get(oid) for f in frames)]
    if not motion_ids:
        motion_ids = object_ids

    state_keys: list[str] = []
    change_indices = [0]
    prev_key: str | None = None
    for i, frame in enumerate(frames):
        key = _visual_state_key(frame, motion_ids)
        state_keys.append(key)
        if key != prev_key:
            change_indices.append(i)
            prev_key = key
    if change_indices and change_indices[-1] != len(frames) - 1:
        change_indices.append(len(frames) - 1)

    unique_pose_count = len(set(state_keys))
    meaningful_keyframes = extract_meaningful_keyframe_indices(frames, motion_ids)
    meaningful_pose_count = len(meaningful_keyframes)

    longest_freeze = 1
    run_start = 0
    for i in range(1, len(state_keys)):
        if state_keys[i] == state_keys[i - 1]:
            run_len = i - run_start + 1
            longest_freeze = max(longest_freeze, run_len)
        else:
            run_start = i

    jump_frames: list[int] = []
    pair_deltas: list[dict[str, Any]] = []
    object_motion_totals: dict[str, float] = {oid: 0.0 for oid in motion_ids}

    pos_eps = 1e-4
    ang_eps = 1e-3
    jump_pos = 0.05
    jump_ang = 0.15

    for i in range(1, len(frames)):
        delta = _aggregate_delta(frames[i - 1], frames[i], motion_ids)
        pair_deltas.append({"frame": i, **delta})
        for oid, d in delta["per_object"].items():
            object_motion_totals[oid] = object_motion_totals.get(oid, 0.0) + d
        if delta["max_pos"] > jump_pos or delta["max_ang"] > jump_ang:
            jump_frames.append(i)

    top_moving = sorted(object_motion_totals.items(), key=lambda x: x[1], reverse=True)[:5]
    top_moving_objects = [{"id": oid, "total_delta": round(v, 6)} for oid, v in top_moving if v > 0]

    identical_ratio = 1.0 - (unique_pose_count / max(1, len(frames)))
    recorder_issue = "none"
    if unique_pose_count <= max(3, len(frames) // 20):
        recorder_issue = "repeated_transforms"
    elif unique_pose_count < len(frames) * 0.25:
        recorder_issue = "upstream_demo_hold"
    elif meaningful_pose_count < max(4, len(frames) // 8) and unique_pose_count >= len(frames) * 0.85:
        recorder_issue = "sparse_motion_phases"

    qpos_counts = [len(f.get("qpos") or {}) for f in frames]
    sample_qpos = {
        "frame_0": frames[0].get("qpos"),
        "frame_mid": frames[len(frames) // 2].get("qpos"),
        "frame_last": frames[-1].get("qpos"),
    }

    primary_motion_link = top_moving_objects[0]["id"] if top_moving_objects else None
    frozen_runs = find_frozen_runs(frames, motion_ids)
    perceptual_longest = max((r["length"] for r in frozen_runs), default=1)
    first_motion = find_first_motion_index(frames, motion_ids)
    last_motion = find_last_motion_index(frames, motion_ids)
    frozen_head = first_motion
    frozen_tail = max(0, len(frames) - 1 - last_motion)
    moving_frame_count = count_moving_frames(frames, motion_ids)

    return {
        "total_frames": len(frames),
        "unique_pose_count": unique_pose_count,
        "meaningful_pose_count": meaningful_pose_count,
        "meaningful_keyframes": meaningful_keyframes,
        "longest_freeze_run": longest_freeze,
        "perceptual_longest_freeze_run": perceptual_longest,
        "frozen_head_length": frozen_head,
        "frozen_tail_length": frozen_tail,
        "moving_frame_count": moving_frame_count,
        "frozen_runs": frozen_runs[:20],
        "jump_frames": jump_frames[:20],
        "jump_count": len(jump_frames),
        "change_indices": change_indices[:20],
        "top_moving_objects": top_moving_objects,
        "primary_motion_link": primary_motion_link,
        "identical_frame_ratio": round(identical_ratio, 4),
        "recorder_issue": recorder_issue,
        "qpos_frame_counts": qpos_counts[:5],
        "qpos_samples": sample_qpos,
        "tracked_object_count": len(motion_ids),
    }


def should_generate_smooth_preview(motion_diag: dict[str, Any], raw_frame_count: int) -> bool:
    """Decide whether to build a non-raw preview timeline from raw replay frames."""
    return choose_preview_mode(motion_diag, raw_frame_count) != "raw"


def choose_preview_mode(motion_diag: dict[str, Any], raw_frame_count: int) -> str:
    """Pick preview strategy: raw, dense_trim (keep motion frames), or smooth_keyframes."""
    if raw_frame_count <= 1:
        return "raw"
    unique = int(motion_diag.get("unique_pose_count") or raw_frame_count)
    meaningful = int(motion_diag.get("meaningful_pose_count") or unique)
    freeze = int(motion_diag.get("perceptual_longest_freeze_run") or motion_diag.get("longest_freeze_run") or 1)
    issue = str(motion_diag.get("recorder_issue") or "none")

    if unique >= raw_frame_count * 0.85 and meaningful < max(4, raw_frame_count // 4):
        return "dense_trim"
    if issue in ("upstream_demo_hold", "repeated_transforms"):
        return "smooth_keyframes"
    if unique < raw_frame_count * 0.85:
        return "smooth_keyframes"
    if meaningful < raw_frame_count * 0.85:
        return "smooth_keyframes"
    if freeze > 3:
        return "smooth_keyframes"
    return "raw"


def log_motion_diagnostics(diagnostics: dict[str, Any]) -> None:
    total = diagnostics.get("total_frames", 0)
    unique = diagnostics.get("unique_pose_count", 0)
    meaningful = diagnostics.get("meaningful_pose_count", unique)
    freeze = diagnostics.get("longest_freeze_run", 0)
    jumps = diagnostics.get("jump_frames", [])
    issue = diagnostics.get("recorder_issue", "unknown")
    primary = diagnostics.get("primary_motion_link") or "none"
    jump_at = jumps[0] if jumps else "none"
    print(
        f"[showcase_launcher] Replay diagnostics: {total} frames, {unique} unique poses, "
        f"{meaningful} meaningful keyframes, longest freeze {freeze} frames, "
        f"jump at frame {jump_at}, primary motion={primary}, issue={issue}",
        flush=True,
    )
    if unique < total * 0.5:
        print(
            "[showcase_launcher] Recorder captured repeated transforms; playback is not the root cause.",
            flush=True,
        )
    if issue in ("upstream_demo_hold", "sparse_motion_phases"):
        if issue == "upstream_demo_hold":
            print(
                "[showcase_launcher] Demo has sparse motion phases; smooth preview will interpolate between keyframes.",
                flush=True,
            )
        else:
            print(
                "[showcase_launcher] Demo has dense micro-motion; preview will preserve per-step finger/object motion.",
                flush=True,
            )
