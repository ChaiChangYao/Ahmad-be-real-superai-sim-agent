from __future__ import annotations

from pathlib import Path

from app.models.manifest import BuildablesPhysicsManifest
from app.services.tests.test_runner_common import run_via_scenario


def run_control_script(project_dir: Path, manifest: BuildablesPhysicsManifest) -> dict:
    return run_via_scenario(project_dir, manifest, "free_drive")
