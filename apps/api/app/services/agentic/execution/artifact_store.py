"""Artifact indexing and safe path resolution."""
from __future__ import annotations

import json
from pathlib import Path

from app.services.agentic.execution.run_store import run_dir
from app.services.agentic.execution.schemas import RunArtifact


def _resolve_under_run(run_root: Path, rel: str) -> Path:
    safe = rel.replace("\\", "/").lstrip("/")
    if ".." in safe:
        raise ValueError(f"Invalid path: {rel}")
    resolved = (run_root / safe).resolve()
    if run_root.resolve() not in resolved.parents and resolved != run_root.resolve():
        raise ValueError(f"Path outside run directory: {rel}")
    return resolved


def list_artifacts(project_id: str, run_id: str) -> list[RunArtifact]:
    root = run_dir(project_id, run_id).resolve()
    if not root.is_dir():
        return []
    artifacts: list[RunArtifact] = []
    mapping = {
        "run.json": "manifest",
        "manifest.json": "manifest",
        "stdout.log": "stdout",
        "stderr.log": "stderr",
        "combined.log": "log",
        "state_timeseries.json": "replay",
        "telemetry_timeseries.json": "telemetry",
        "report.json": "report",
        "generated/script.py": "generated_script",
        "generated/script.context.json": "context",
    }
    for rel, kind in mapping.items():
        p = root / rel.replace("/", "\\") if "\\" in str(root) else root / rel
        if p.is_file():
            artifacts.append(
                RunArtifact(
                    artifact_id=f"{run_id}:{kind}",
                    run_id=run_id,
                    kind=kind,
                    path=str(p),
                    size_bytes=p.stat().st_size,
                    content_type="application/json" if p.suffix == ".json" else "text/plain",
                    created_at="",
                )
            )
    art_dir = root / "artifacts"
    if art_dir.is_dir():
        for f in art_dir.rglob("*"):
            if f.is_file():
                rel = str(f.relative_to(root)).replace("\\", "/")
                artifacts.append(
                    RunArtifact(
                        artifact_id=f"{run_id}:artifact:{rel}",
                        run_id=run_id,
                        kind="artifact",
                        path=str(f),
                        size_bytes=f.stat().st_size,
                    )
                )
    return artifacts


def read_artifact_file(project_id: str, run_id: str, relative_path: str) -> bytes:
    root = run_dir(project_id, run_id).resolve()
    path = _resolve_under_run(root, relative_path)
    if not path.is_file():
        raise FileNotFoundError(relative_path)
    return path.read_bytes()


def read_manifest(project_id: str, run_id: str, *, allow_partial: bool = False) -> dict:
    root = run_dir(project_id, run_id)
    path = root / "manifest.json"
    if not path.is_file():
        raise FileNotFoundError("manifest.json not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    status = str(data.get("status") or "")
    if not allow_partial and status not in ("complete", "failed"):
        raise FileNotFoundError(f"Manifest not final (status={status})")
    return data


def read_replay(project_id: str, run_id: str, *, allow_partial: bool = False) -> dict:
    from app.services.genesis_showcase.replay_atomic_io import effective_timeseries_path, read_manifest as read_replay_manifest

    root = run_dir(project_id, run_id)
    manifest = read_replay_manifest(root) or read_manifest(project_id, run_id, allow_partial=allow_partial)
    if not allow_partial:
        mstatus = str(manifest.get("status") or "")
        visual = manifest.get("visual") or {}
        if mstatus != "complete" and not visual.get("hasReplay"):
            raise FileNotFoundError("Replay not ready")
    ts_path = effective_timeseries_path(root, manifest if isinstance(manifest, dict) else None)
    if not ts_path.is_file():
        raise FileNotFoundError("state_timeseries.json not found")
    return json.loads(ts_path.read_text(encoding="utf-8"))


def read_telemetry(project_id: str, run_id: str, *, allow_partial: bool = False) -> dict:
    root = run_dir(project_id, run_id)
    path = root / "telemetry_timeseries.json"
    if not path.is_file():
        if not allow_partial:
            manifest = read_manifest(project_id, run_id, allow_partial=True)
            if not (manifest.get("telemetry") or {}).get("hasTelemetry"):
                raise FileNotFoundError("No telemetry for this run")
        raise FileNotFoundError("telemetry_timeseries.json not found")
    return json.loads(path.read_text(encoding="utf-8"))
