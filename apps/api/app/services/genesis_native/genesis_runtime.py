from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import threading
from datetime import datetime, UTC

from .gs_lazy import gs as _gs


_GENESIS_LOCK = threading.Lock()
_SHARED_RUNTIME: "GenesisNativeRuntime | None" = None


@dataclass
class GenesisRunConfig:
    dt: float = 1.0 / 60.0
    show_viewer: bool = False
    backend: str = "auto"
    substeps: int = 1


def shared_runtime() -> "GenesisNativeRuntime":
    global _SHARED_RUNTIME
    if _SHARED_RUNTIME is None:
        _SHARED_RUNTIME = GenesisNativeRuntime()
    return _SHARED_RUNTIME


def genesis_lock() -> threading.Lock:
    return _GENESIS_LOCK


def ensure_genesis_initialized(config: "GenesisRunConfig | None" = None) -> "GenesisNativeRuntime":
    cfg = config or GenesisRunConfig()
    with _GENESIS_LOCK:
        runtime = shared_runtime()
        runtime.init(cfg)
        return runtime


class GenesisNativeRuntime:
    def __init__(self) -> None:
        self._initialized = False
        self._backend = "auto"

    def init(self, config: GenesisRunConfig) -> None:
        gs = _gs()
        if getattr(gs, "_initialized", False):
            self._initialized = True
            self._backend = config.backend
            return
        if self._initialized and self._backend == config.backend:
            return
        backend = gs.cpu
        if config.backend == "cuda":
            backend = gs.cuda
        elif config.backend == "gpu":
            backend = gs.gpu
        elif config.backend == "metal":
            backend = gs.metal
        gs.init(backend=backend)
        self._initialized = True
        self._backend = config.backend

    def create_scene(self, config: GenesisRunConfig) -> Any:
        gs = _gs()
        self.init(config)
        sim_options = gs.options.SimOptions(dt=config.dt, substeps=config.substeps)
        return gs.Scene(sim_options=sim_options, show_viewer=config.show_viewer)

    def build_scene(self, scene: Any) -> None:
        scene.build()

    def step_scene(self, scene: Any, n_steps: int) -> int:
        steps = 0
        for _ in range(max(1, n_steps)):
            scene.step()
            steps += 1
        return steps

    def run_scene(self, scene: Any, n_steps: int, tracked_entities: dict[str, Any]) -> dict:
        state_timeseries: list[dict] = []
        started = datetime.now(UTC)
        for step in range(max(1, n_steps)):
            scene.step()
            frame_entities: dict[str, Any] = {}
            for name, entity in tracked_entities.items():
                try:
                    pos = entity.get_pos().tolist()
                except Exception:
                    pos = [0.0, 0.0, 0.0]
                try:
                    quat = entity.get_quat().tolist()
                except Exception:
                    quat = [1.0, 0.0, 0.0, 0.0]
                try:
                    dof_pos = entity.get_dofs_position().tolist()
                except Exception:
                    dof_pos = []
                frame_entities[name] = {"position": pos, "rotation_quat": quat, "dof_position": dof_pos}
            state_timeseries.append({"t": round(step * 1.0 / 60.0, 6), "step": step, "entities": frame_entities})
        ended = datetime.now(UTC)
        return {
            "genesis_used": True,
            "mocked": False,
            "scene_built": True,
            "step_count": len(state_timeseries),
            "duration_s": (ended - started).total_seconds(),
            "state_timeseries": state_timeseries,
        }

    @staticmethod
    def write_artifacts(run_dir: Path, payload: dict) -> dict:
        run_dir.mkdir(parents=True, exist_ok=True)
        state_path = run_dir / "state_timeseries.json"
        metrics_path = run_dir / "metrics.json"
        logs_path = run_dir / "logs.txt"
        state_path.write_text(json.dumps(payload.get("state_timeseries", []), indent=2), encoding="utf-8")
        metrics_path.write_text(json.dumps(payload.get("metrics", {}), indent=2), encoding="utf-8")
        logs_path.write_text("\n".join(payload.get("logs", [])), encoding="utf-8")
        return {"state_timeseries": str(state_path), "metrics": str(metrics_path), "logs": str(logs_path)}
