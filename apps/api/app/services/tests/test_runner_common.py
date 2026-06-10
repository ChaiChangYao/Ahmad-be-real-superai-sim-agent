from __future__ import annotations

from pathlib import Path

from app.models.manifest import BuildablesPhysicsManifest
from app.services.genesis.scenario_runner import run_scenario_sync


def run_via_scenario(project_dir_path: Path, manifest: BuildablesPhysicsManifest, scenario_id: str) -> dict:
    scenario = next((s for s in manifest.scenarios if s.id == scenario_id), None)
    if not scenario:
        raise RuntimeError(f"Scenario not found for mapped test: {scenario_id}")
    return run_scenario_sync(project_dir_path, manifest, scenario)
