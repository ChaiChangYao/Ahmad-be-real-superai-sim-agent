from __future__ import annotations

from pathlib import Path

from app.models.manifest import BuildablesPhysicsManifest
from app.services.tests.test_runner_common import run_via_scenario


def run_joint_sweep(project_dir: Path, manifest: BuildablesPhysicsManifest) -> dict:
    return run_via_scenario(project_dir, manifest, "joint_sweep_collision")


def run_mechanism_motion(project_dir: Path, manifest: BuildablesPhysicsManifest) -> dict:
    return run_via_scenario(project_dir, manifest, "walk_forward")
