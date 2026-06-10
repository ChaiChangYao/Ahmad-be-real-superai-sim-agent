"""Capture sensor telemetry alongside visual replay frames."""

from __future__ import annotations

import json
import os
from pathlib import Path

from typing import Any



IMU_CHANNEL_NAMES = ("lin_acc", "true_lin_acc", "ang_vel", "true_ang_vel")



IMU_FLAT_CHANNELS = tuple(f"{name}.{axis}" for name in IMU_CHANNEL_NAMES for axis in ("x", "y", "z"))





def _as_float3(value: Any) -> list[float]:

    if value is None:

        return [0.0, 0.0, 0.0]

    if hasattr(value, "detach"):

        value = value.detach()

    if hasattr(value, "cpu"):

        value = value.cpu()

    if hasattr(value, "numpy"):

        value = value.numpy()

    if hasattr(value, "tolist"):

        value = value.tolist()

    if isinstance(value, dict):

        if all(k in value for k in ("x", "y", "z")):

            return [float(value["x"]), float(value["y"]), float(value["z"])]

    if isinstance(value, (list, tuple)):

        if value and isinstance(value[0], (list, tuple)):

            value = value[0]

        return [float(value[i]) if i < len(value) else 0.0 for i in range(3)]

    return [0.0, 0.0, 0.0]





def _flatten_sample(sample: dict[str, Any]) -> dict[str, list[float]]:

    flat: dict[str, list[float]] = {}

    for key, value in sample.items():

        if key in ("t", "step"):

            continue

        if isinstance(value, dict):

            if all(axis in value for axis in ("x", "y", "z")):

                flat[key] = [float(value["x"]), float(value["y"]), float(value["z"])]

            else:

                for sub_key, sub_val in value.items():

                    flat[f"{key}.{sub_key}"] = _as_float3(sub_val)

        else:

            flat[key] = _as_float3(value)

    return flat





def build_imu_telemetry_sample(imu: Any) -> dict[str, Any]:

    """Read measured + ground-truth IMU vectors (matches imu_franka.py native plot path)."""

    data = imu.read()

    true_data = imu.read_ground_truth()

    return {

        "lin_acc": getattr(data, "lin_acc", None),

        "true_lin_acc": getattr(true_data, "lin_acc", None),

        "ang_vel": getattr(data, "ang_vel", None),

        "true_ang_vel": getattr(true_data, "ang_vel", None),

    }





def _find_imu_npz(search_dirs: list[Path]) -> Path | None:

    seen: set[str] = set()

    for directory in search_dirs:

        try:

            resolved = str(directory.resolve())

        except OSError:

            continue

        if resolved in seen:

            continue

        seen.add(resolved)

        candidate = directory / "imu_data.npz"

        if candidate.is_file():

            return candidate

    return None





class TelemetryRecorder:

    def __init__(self, *, sample_rate: float = 100.0, playback_rate: float = 24.0) -> None:

        self.sample_rate = sample_rate

        self.playback_rate = playback_rate

        self.timestamps: list[float] = []

        self.steps: list[int] = []

        self.channels: dict[str, dict[str, list[float]]] = {}

        self._dt = 0.01

        self._sample_index = 0

        self.imu_capture_active = False

        self.depth_frames: list[dict[str, str]] = []

        self.tactile_frames: list[dict[str, Any]] = []



    def set_dt(self, dt: float) -> None:

        if dt > 0:

            self._dt = dt

            self.sample_rate = round(1.0 / dt)



    def append_sample(

        self,

        sample: dict[str, Any],

        *,

        t: float | None = None,

        step: int | None = None,

    ) -> None:

        if not sample:

            return

        flat = _flatten_sample(sample)

        ts = float(t if t is not None else self._sample_index * self._dt)

        step_idx = int(step if step is not None else self._sample_index)

        self.timestamps.append(ts)

        self.steps.append(step_idx)

        for channel, vec in flat.items():

            bucket = self.channels.setdefault(channel, {"x": [], "y": [], "z": []})

            bucket["x"].append(vec[0])

            bucket["y"].append(vec[1])

            bucket["z"].append(vec[2])

        self._sample_index += 1

    def append_depth_frame(
        self,
        frames: dict[str, str],
        *,
        t: float | None = None,
        step: int | None = None,
    ) -> None:
        if not frames:
            return
        self.depth_frames.append(dict(frames))
        if not self.timestamps and t is not None:
            self.timestamps.append(float(t))
            self.steps.append(int(step if step is not None else len(self.depth_frames) - 1))

    def append_tactile_frame(
        self,
        frame: dict[str, Any],
        *,
        t: float | None = None,
        step: int | None = None,
    ) -> None:
        if not frame:
            return
        self.tactile_frames.append(dict(frame))
        if not self.timestamps and t is not None:
            self.timestamps.append(float(t))
            self.steps.append(int(step if step is not None else len(self.tactile_frames) - 1))



    def sample_count(self) -> int:

        return len(self.timestamps)



    def _build_imu_schema(self) -> dict[str, Any] | None:

        if not self.timestamps:

            return None

        if not any(name in self.channels for name in IMU_CHANNEL_NAMES):

            return None

        samples: list[dict[str, Any]] = []

        for idx, ts in enumerate(self.timestamps):

            step = self.steps[idx] if idx < len(self.steps) else idx

            entry: dict[str, Any] = {"t": ts, "step": step}

            for name in IMU_CHANNEL_NAMES:

                bucket = self.channels.get(name) or {"x": [], "y": [], "z": []}

                entry[name] = [

                    bucket["x"][idx] if idx < len(bucket["x"]) else 0.0,

                    bucket["y"][idx] if idx < len(bucket["y"]) else 0.0,

                    bucket["z"][idx] if idx < len(bucket["z"]) else 0.0,

                ]

            samples.append(entry)

        return {

            "type": "imu",

            "sampleRate": self.sample_rate,

            "channels": list(IMU_FLAT_CHANNELS),

            "samples": samples,

        }



    def to_bundle(self) -> dict[str, Any] | None:

        if not self.timestamps:

            return None

        bundle: dict[str, Any] = {

            "sampleRate": self.sample_rate,

            "playbackRate": self.playback_rate,

            "timestamps": self.timestamps,

            "channels": self.channels,

        }

        imu_schema = self._build_imu_schema()

        if imu_schema is not None:

            bundle["imu"] = imu_schema

            bundle["type"] = "imu"

        if self.depth_frames:

            bundle["depth_frames"] = self.depth_frames

            bundle["type"] = "depth_camera"

        if self.tactile_frames:

            bundle["tactile_frames"] = self.tactile_frames

            bundle["type"] = "tactile"

        if self.channels and any(name in self.channels for name in ("force", "RR_foot", "FR_foot")):

            bundle["type"] = "contact_force"

        return bundle



    def diagnostics(self) -> dict[str, Any]:

        count = self.sample_count()

        distinct = count

        longest_repeat = 0

        if count > 1:

            distinct = 1

            run = 1

            prev_key: tuple[tuple[str, float], ...] | None = None

            for idx in range(count):

                key = tuple(

                    (name, round(self.channels[name]["x"][idx], 8))

                    for name in sorted(self.channels)

                    if self.channels[name]["x"]

                )

                if prev_key is not None and key == prev_key:

                    run += 1

                    longest_repeat = max(longest_repeat, run)

                else:

                    distinct += 0 if prev_key is None else 1

                    run = 1

                prev_key = key

            if count == 1:

                distinct = 1

        return {

            "telemetry_sample_count": count,

            "telemetry_distinct_sample_count": distinct if count else 0,

            "longest_repeated_telemetry_run": longest_repeat,

            "telemetry_trim_applied": False,

        }





def load_npz_telemetry_fallback(run_dir: Path) -> dict[str, Any] | None:

    search_dirs = [run_dir, run_dir.parent, Path.cwd()]

    npz_path = _find_imu_npz(search_dirs)

    if npz_path is None:

        return None

    try:

        import numpy as np



        data = np.load(npz_path, allow_pickle=True)

        recorder = TelemetryRecorder()

        keys = [str(k) for k in data.files if not str(k).startswith("_")]

        if not keys:

            return None

        length = len(data[keys[0]])

        for idx in range(length):

            sample: dict[str, Any] = {}

            for key in keys:

                arr = data[key]

                if arr.ndim == 1:

                    sample[key] = [float(arr[idx]), 0.0, 0.0]

                else:

                    sample[key] = [float(arr[idx, i]) for i in range(min(3, arr.shape[1]))]

            recorder.append_sample(sample, t=idx * recorder._dt, step=idx)

        bundle = recorder.to_bundle()

        if bundle:

            bundle["source"] = str(npz_path.name)

        return bundle

    except Exception as exc:

        print(f"[showcase_launcher] Telemetry NPZ fallback failed: {exc}", flush=True)

        return None


def chart_bundle_from_imu_schema(imu_schema: dict[str, Any]) -> dict[str, Any] | None:
    samples = imu_schema.get("samples")
    if not isinstance(samples, list) or not samples:
        return None
    recorder = TelemetryRecorder(sample_rate=float(imu_schema.get("sampleRate") or 100))
    for sample in samples:
        if not isinstance(sample, dict):
            continue
        payload = {key: sample[key] for key in IMU_CHANNEL_NAMES if key in sample}
        if not payload:
            continue
        recorder.append_sample(
            payload,
            t=float(sample.get("t", 0.0)),
            step=int(sample.get("step", recorder.sample_count())),
        )
    bundle = recorder.to_bundle()
    if bundle:
        bundle["source"] = "telemetry_timeseries.json"
    return bundle


def load_telemetry_for_run(out_dir: Path) -> dict[str, Any] | None:
    ts_path = out_dir / "state_timeseries.json"
    if ts_path.is_file():
        try:
            raw = json.loads(ts_path.read_text(encoding="utf-8"))
            tele = raw.get("telemetry")
            if isinstance(tele, dict):
                timestamps = tele.get("timestamps") or []
                channels = tele.get("channels") or {}
                if timestamps and channels:
                    return tele
                imu_block = tele.get("imu")
                if isinstance(imu_block, dict):
                    chart = chart_bundle_from_imu_schema(imu_block)
                    if chart:
                        return chart
        except Exception as exc:
            print(f"[showcase_launcher] Telemetry read from state_timeseries failed: {exc}", flush=True)

    companion = out_dir / "telemetry_timeseries.json"
    if companion.is_file():
        try:
            imu_schema = json.loads(companion.read_text(encoding="utf-8"))
            if isinstance(imu_schema, dict):
                chart = chart_bundle_from_imu_schema(imu_schema)
                if chart:
                    return chart
        except Exception as exc:
            print(f"[showcase_launcher] Telemetry read from companion file failed: {exc}", flush=True)
    return None


def write_telemetry_companion(out_dir: Path, telemetry: dict[str, Any] | None, *, partial: bool = False) -> None:

    if partial or not telemetry:

        return

    imu_block = telemetry.get("imu")

    if not isinstance(imu_block, dict):

        return

    path = out_dir / "telemetry_timeseries.json"

    path.write_text(json.dumps(imu_block, indent=2), encoding="utf-8")





def _is_native_plot_recorder(recorder: Any) -> bool:

    name = type(recorder).__name__

    return any(token in name for token in ("MPLLinePlot", "PyQtLinePlot", "LinePlot"))





def install_telemetry_capture(

    recorder: TelemetryRecorder,

    *,

    disable_native_plots: bool | None = None,

) -> None:

    """Patch Genesis scene.start_recording to capture sensor callbacks and skip native plots."""

    import genesis as gs



    if getattr(gs.Scene.start_recording, "_buildables_telemetry_patch", False):

        return



    original = gs.Scene.start_recording

    disable = disable_native_plots if disable_native_plots is not None else os.environ.get("BUILDABLES_DISABLE_NATIVE_PLOTS") == "1"



    def patched_start_recording(self, data_func, rec_options=None, **kwargs):

        if rec_options is None:

            rec_options = kwargs.get("rec_options")

        if rec_options is None:

            raise TypeError("start_recording() missing required argument: 'rec_options'")



        target = rec_options



        if disable and target is not None and _is_native_plot_recorder(target):

            print(

                f"[showcase_launcher] Skipped native plot recorder: {type(target).__name__}",

                flush=True,

            )

            if callable(data_func) and not recorder.imu_capture_active:

                try:

                    payload = data_func()

                    if isinstance(payload, dict) and payload:

                        recorder.append_sample(payload)

                except Exception:

                    pass

            return None



        wrapped_func = data_func

        if callable(data_func) and not recorder.imu_capture_active:



            def wrapped_func():

                payload = data_func()

                if isinstance(payload, dict) and payload:

                    recorder.append_sample(payload)

                return payload



        return original(self, wrapped_func, rec_options)



    patched_start_recording._buildables_telemetry_patch = True  # type: ignore[attr-defined]

    gs.Scene.start_recording = patched_start_recording  # type: ignore[method-assign]


def install_headless_plot_hooks() -> None:
    """No-op native plot/display hooks during web recording."""
    if os.environ.get("BUILDABLES_WEB_RECORD") != "1" and os.environ.get("BUILDABLES_DISABLE_NATIVE_PLOTS") != "1":
        return
    try:
        import matplotlib.pyplot as plt

        plt.show = lambda *args, **kwargs: None  # type: ignore[assignment, misc]
    except Exception:
        pass
    try:
        import cv2

        cv2.imshow = lambda *args, **kwargs: None  # type: ignore[assignment, misc]
        cv2.waitKey = lambda *args, **kwargs: 0  # type: ignore[assignment, misc]
    except Exception:
        pass

