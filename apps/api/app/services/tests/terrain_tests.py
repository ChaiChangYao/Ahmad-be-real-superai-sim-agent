from __future__ import annotations

from pathlib import Path

from app.models.manifest import BuildablesPhysicsManifest
from app.services.tests.test_runner_common import run_via_scenario


def run_slope(project_dir: Path, manifest: BuildablesPhysicsManifest) -> dict:
    return run_via_scenario(project_dir, manifest, "slope_climb")


def run_rough(project_dir: Path, manifest: BuildablesPhysicsManifest) -> dict:
    return run_via_scenario(project_dir, manifest, "rough_terrain")
