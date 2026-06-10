from __future__ import annotations

from pathlib import Path

from app.models.manifest import BuildablesPhysicsManifest, Scenario
from app.services.genesis_native.scenario_executor import (
    apply_joint_command,
    list_project_dofs,
    run_genesis_interactive_segment,
    run_genesis_scenario,
)


def run_scenario_sync(project_dir: Path, manifest: BuildablesPhysicsManifest, scenario: Scenario, *, test_id: str | None = None) -> dict:
    return run_genesis_scenario(project_dir, manifest, scenario, test_id=test_id)


def run_interactive_segment(manifest: BuildablesPhysicsManifest, command: str, duration_s: float = 0.35, *, project_dir: Path | None = None) -> dict:
    if project_dir is None:
        from app.services.project_store import project_dir as resolve_project_dir

        project_dir = resolve_project_dir(manifest.project_id)
    return run_genesis_interactive_segment(project_dir, manifest, command, duration_s)
