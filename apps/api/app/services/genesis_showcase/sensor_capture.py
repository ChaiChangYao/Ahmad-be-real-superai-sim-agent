"""Helpers for capturing typed sensor payloads during web replay recording."""
from __future__ import annotations

import base64
import io
from typing import Any

CONTACT_FOOT_ORDER = ("FR_foot", "FL_foot", "RR_foot", "RL_foot")
DEPTH_CAMERA_NAMES = ("robot", "world")


def tensor_to_array(value: Any):
    if value is None:
        return None
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        return value.numpy()
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def as_float3(value: Any) -> list[float]:
    if value is None:
        return [0.0, 0.0, 0.0]
    arr = tensor_to_array(value)
    if isinstance(arr, dict) and all(k in arr for k in ("x", "y", "z")):
        return [float(arr["x"]), float(arr["y"]), float(arr["z"])]
    if isinstance(arr, (list, tuple)):
        if arr and isinstance(arr[0], (list, tuple)):
            arr = arr[0]
        return [float(arr[i]) if i < len(arr) else 0.0 for i in range(3)]
    return [0.0, 0.0, 0.0]


def extract_lidar_points(sensor: Any, *, max_points: int = 2500) -> list[list[float]]:
    import numpy as np

    try:
        data = sensor.read()
    except Exception:
        return []

    points = data
    for attr in ("points", "hit_points", "positions", "pts"):
        if hasattr(data, attr):
            points = getattr(data, attr)
            break
    if isinstance(data, (list, tuple)) and data:
        candidate = data[0]
        if hasattr(candidate, "shape") or isinstance(candidate, (list, tuple)):
            points = candidate

    arr = np.asarray(tensor_to_array(points), dtype=np.float64)
    if arr.size == 0:
        return []

    if arr.ndim == 1:
        if arr.size % 3 != 0:
            return []
        arr = arr.reshape(-1, 3)
    elif arr.ndim >= 2:
        arr = arr.reshape(-1, arr.shape[-1])
        if arr.shape[-1] < 3:
            return []
        arr = arr[:, :3]

    finite = np.isfinite(arr).all(axis=1)
    arr = arr[finite]
    if arr.shape[0] == 0:
        return []

    if arr.shape[0] > max_points:
        idx = np.linspace(0, arr.shape[0] - 1, max_points, dtype=int)
        arr = arr[idx]

    return [[float(p[0]), float(p[1]), float(p[2])] for p in arr]


def encode_depth_heatmap(
    depth: Any,
    *,
    vmin: float = 0.0,
    vmax: float = 5.0,
    title: str = "",
    max_size: int = 160,
) -> str:
    import numpy as np

    arr = np.asarray(tensor_to_array(depth), dtype=np.float64)
    while arr.ndim > 2:
        arr = arr[0]

    if arr.ndim != 2:
        return ""

    finite = np.isfinite(arr)
    if not finite.any():
        arr = np.zeros_like(arr)
    else:
        arr = np.where(finite, arr, vmax)

    h, w = arr.shape
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        ys = np.linspace(0, h - 1, new_h).astype(int)
        xs = np.linspace(0, w - 1, new_w).astype(int)
        arr = arr[np.ix_(ys, xs)]

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return ""

    fig, ax = plt.subplots(figsize=(3.2, 2.6), facecolor="white")
    im = ax.imshow(arr, vmin=vmin, vmax=vmax, cmap="plasma", aspect="auto")
    ax.set_title(title, fontsize=9)
    ax.set_xticks([])
    ax.set_yticks([])
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("depth (m)", fontsize=8)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white", dpi=96)
    plt.close(fig)
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def capture_depth_cameras(
    cameras: list[tuple[str, Any]],
    *,
    vmin: float = 0.0,
    vmax: float = 5.0,
) -> dict[str, str]:
    frames: dict[str, str] = {}
    for name, sensor in cameras:
        try:
            img = sensor.read_image()
        except Exception:
            continue
        title = f"Depth - {name} cam"
        data_url = encode_depth_heatmap(img, vmin=vmin, vmax=vmax, title=title)
        if data_url:
            frames[name] = data_url
    return frames


def capture_tactile_frame(sensor: Any) -> dict[str, Any] | None:
    import numpy as np

    try:
        data = sensor.read()
    except Exception:
        return None

    disp = np.asarray(tensor_to_array(data), dtype=np.float64)
    if disp.size == 0:
        return None

    if disp.ndim >= 3:
        disp = disp[0]
    if disp.ndim >= 2:
        disp = disp.reshape(-1, disp.shape[-1])
    elif disp.ndim == 1:
        if disp.size % 3 == 0:
            disp = disp.reshape(-1, 3)
        else:
            disp = disp.reshape(-1, 1)

    positions = getattr(sensor, "probe_local_pos", None)
    if positions is None:
        options = getattr(sensor, "_options", None) or getattr(sensor, "options", None)
        positions = getattr(options, "probe_local_pos", None) if options is not None else None

    pos_arr = np.asarray(tensor_to_array(positions), dtype=np.float64) if positions is not None else None
    if pos_arr is not None and pos_arr.size > 0:
        pos_arr = pos_arr.reshape(-1, 3)
        count = min(pos_arr.shape[0], disp.shape[0])
        pos_arr = pos_arr[:count]
        disp = disp[:count]
    else:
        count = disp.shape[0]
        side = int(np.sqrt(count))
        xs = np.linspace(-0.05, 0.05, side if side * side == count else count)
        ys = np.linspace(-0.075, 0.075, side if side * side == count else count)
        if side * side == count:
            gx, gy = np.meshgrid(xs, ys)
            pos_arr = np.stack([gx.ravel(), gy.ravel(), np.zeros(count)], axis=-1)
        else:
            pos_arr = np.stack([xs, np.zeros(count), np.zeros(count)], axis=-1)

    if disp.shape[-1] >= 3:
        magnitudes = np.linalg.norm(disp[:, :3], axis=1)
        displacements = disp[:, :3]
    else:
        magnitudes = np.abs(disp[:, 0])
        displacements = np.stack([disp[:, 0], np.zeros(count), np.zeros(count)], axis=-1)

    return {
        "positions": pos_arr.tolist(),
        "displacements": displacements.tolist(),
        "magnitudes": magnitudes.tolist(),
    }


def capture_contact_force_sample(sensors: list[tuple[str, Any]]) -> dict[str, list[float]]:
    sample: dict[str, list[float]] = {}
    total = [0.0, 0.0, 0.0]
    for link_name, sensor in sensors:
        try:
            data = sensor.read()
        except Exception:
            continue
        vec = as_float3(data)
        sample[link_name] = vec
        total[0] += vec[0]
        total[1] += vec[1]
        total[2] += vec[2]
    if sample:
        sample["force"] = total
    return sample
