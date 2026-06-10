from __future__ import annotations

from pathlib import Path

from app.models.manifest import BuildablesPhysicsManifest
from app.services.tests.test_runner_common import run_via_scenario


def run_camera_render(project_dir: Path, manifest: BuildablesPhysicsManifest) -> dict:
    # Placeholder path uses stand scenario until dedicated renderer artifacts are wired.
    return run_via_scenario(project_dir, manifest, "stand_balance")
