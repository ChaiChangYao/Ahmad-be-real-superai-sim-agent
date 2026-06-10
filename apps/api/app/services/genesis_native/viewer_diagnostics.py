from __future__ import annotations

from dataclasses import dataclass, field

from app.services.genesis.genesis_runtime import genesis_runtime


@dataclass
class ViewerDiagnosticsSampler:
    step_times_ms: list[float] = field(default_factory=list)
    sample_every: int = 30

    def record_step(self, step_s: float) -> None:
        self.step_times_ms.append(step_s * 1000.0)
        if len(self.step_times_ms) > 120:
            self.step_times_ms.pop(0)

    def summary(self) -> dict:
        if not self.step_times_ms:
            return {"physics_step_ms_avg": None, "physics_step_ms_p95": None, "samples": 0}
        ordered = sorted(self.step_times_ms)
        p95_idx = min(len(ordered) - 1, int(len(ordered) * 0.95))
        avg = sum(ordered) / len(ordered)
        return {
            "physics_step_ms_avg": round(avg, 3),
            "physics_step_ms_p95": round(ordered[p95_idx], 3),
            "samples": len(ordered),
        }


def collect_viewer_diagnostics(config_backend: str, step_summary: dict) -> dict:
    status = genesis_runtime.status()
    backend = status.backend or config_backend or "cpu"
    cuda_available = False
    try:
        import torch

        cuda_available = bool(torch.cuda.is_available())
    except Exception:
        cuda_available = False

    warnings: list[str] = []
    if backend.lower() in {"cpu", "gs.cpu"}:
        warnings.append("Native viewer running on CPU backend")
    if not cuda_available:
        warnings.append("CUDA unavailable — web replay recommended for smooth preview")

    return {
        "backend": backend,
        "device": status.device,
        "cuda_available": cuda_available,
        "viewer_warnings": warnings,
        "viewer_diagnostics": step_summary,
    }
