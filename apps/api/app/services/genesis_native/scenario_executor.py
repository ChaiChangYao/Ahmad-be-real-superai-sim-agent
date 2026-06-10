from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
from uuid import uuid4
import json
import math

from typing import Any

from app.models.manifest import BuildablesPhysicsManifest, Scenario
from app.services.controls.jump_controller import jump_targets
from app.services.controls.robot_dog_controller import command_to_targets
from app.services.genesis.genesis_runtime import genesis_runtime
from app.services.cad_import.urdf_generator import generate_urdf
from app.services.genesis.imported_robot_loader import resolve_robot_description_candidates
from app.services.genesis.metrics_collector import collect_metrics, evaluate_status
from app.services.genesis.scene_builder import build_scene_summary
from app.services.genesis_native.base_mode import base_mode_to_fixed, default_base_mode_for_profile
from app.services.genesis_native.entity_loader import add_box, add_from_robot_description, add_plane
from app.services.genesis_native.force_applier import apply_lateral_force
from app.services.genesis_native.genesis_runtime import (
    GenesisNativeRuntime,
    GenesisRunConfig,
    ensure_genesis_initialized,
    genesis_lock,
    shared_runtime,
)
from app.services.genesis_native.joint_controller import apply_joint_targets, list_dofs
from app.services.genesis_native.state_collector import build_frame


PROFILE_FOR_SCENARIO = {
    "stand_balance": "passive_gravity",
    "free_drive": "passive_gravity",
    "joint_sweep_collision": "joint_sweep",
    "walk_forward": "joint_motion",
    "payload_carry": "payload_load",
    "torque_margin": "joint_motion",
    "sensor_visibility": "passive_gravity",
    "component_fit": "passive_gravity",
}

TEST_PROFILE_ALIASES = {
    "lateral-push": "lateral_push",
    "payload-load": "payload_load",
    "passive-gravity": "passive_gravity",
    "joint-sweep": "joint_sweep",
    "joint-slider": "joint_sweep",
    "torque-limit": "joint_motion",
    "moment-stability": "passive_gravity",
    "contact-collision": "joint_sweep",
    "sensor-readout": "passive_gravity",
    "render-camera": "passive_gravity",
    "deformation": "passive_gravity",
    "plane_and_box_drop": "plane_and_box_drop",
    "lateral_push_topple": "lateral_push",
    "payload_failure": "payload_load",
    "free_base_passive_gravity": "passive_gravity",
    "fixed_base_no_topple": "fixed_base_passive",
}


def profile_for_run(scenario: Scenario, test_id: str | None = None) -> str:
    if test_id and test_id in TEST_PROFILE_ALIASES:
        return TEST_PROFILE_ALIASES[test_id]
    if isinstance(scenario.config, dict) and scenario.config.get("genesis_profile"):
        return str(scenario.config["genesis_profile"])
    return PROFILE_FOR_SCENARIO.get(scenario.id, "passive_gravity")


def _joint_ids(manifest: BuildablesPhysicsManifest) -> list[str]:
    return [joint.id for joint in manifest.joints]


def _build_scene_for_project(
    runtime: GenesisNativeRuntime,
    manifest: BuildablesPhysicsManifest,
    project_dir: Path,
    *,
    base_mode: str,
    profile: str,
    payload_kg: float,
) -> tuple[Any, dict[str, Any], str | None]:
    config = GenesisRunConfig(show_viewer=False, dt=1.0 / 60.0)
    scene = runtime.create_scene(config)
    add_plane(scene)
    tracked: dict[str, Any] = {}
    robot_desc_type: str | None = None
    fixed = base_mode_to_fixed(base_mode)

    if profile == "plane_and_box_drop":
        tracked["target"] = add_box(scene, pos=(0.0, 0.0, 1.0), size=(0.2, 0.2, 0.2), fixed=False)
        return scene, tracked, "box"

    if profile == "lateral_push":
        tracked["target"] = add_box(scene, pos=(0.0, 0.0, 1.2), size=(0.12, 0.12, 0.8), fixed=False)
        return scene, tracked, "box"

    from app.services.genesis_native.urdf_mjcf_loader import add_urdf_entity

    pos = (0.0, 0.0, 0.5 if not fixed else 0.0)
    candidates = list(resolve_robot_description_candidates(manifest, project_dir))
    fallback_path = project_dir / "generated" / "robot_description" / "genesis_physics.urdf"
    generate_urdf(manifest, fallback_path)
    fallback_resolved = fallback_path.resolve()
    filtered = [(desc_type, path) for desc_type, path in candidates if str(path) != str(fallback_resolved)]
    candidates = [("urdf", fallback_resolved), *filtered]

    last_error: Exception | None = None
    for desc_type, desc_path in candidates:
        try:
            robot_desc_type = desc_type
            if desc_type == "urdf":
                tracked["robot"] = add_urdf_entity(scene, desc_path, fixed=fixed, pos=pos, euler=(0.0, 0.0, 0.0))
            else:
                tracked["robot"] = add_from_robot_description(scene, desc_path, desc_type, fixed=fixed)
            break
        except Exception as exc:  # noqa: PERF203
            last_error = exc
            tracked.pop("robot", None)
            continue
    else:
        if manifest.project_mode == "imported_project":
            raise RuntimeError(f"Failed to load imported robot description: {last_error}")
        tracked["robot"] = add_box(scene, pos=(0.0, 0.0, 0.8), size=(0.35, 0.25, 0.5), fixed=fixed)
        robot_desc_type = "generated_box"

    if profile == "payload_load" and payload_kg > 0:
        h = max(0.05, 0.04 * payload_kg)
        tracked["payload"] = add_box(scene, pos=(0.0, 0.0, 1.2), size=(0.18, 0.18, h), fixed=False)

    return scene, tracked, robot_desc_type


def _apply_profile_pre_step(
    profile: str,
    step: int,
    total_steps: int,
    tracked: dict[str, Any],
    scenario: Scenario,
    manifest: BuildablesPhysicsManifest,
) -> None:
    robot = tracked.get("robot") or tracked.get("target")
    if robot is None:
        return

    if profile == "joint_sweep":
        dof_info = list_dofs(robot)
        if dof_info["count"] <= 0:
            return
        phase = step / max(1, total_steps - 1)
        targets: list[float] = []
        for idx, limits in enumerate(dof_info["limits"]):
            lo, hi = (limits[0], limits[1]) if len(limits) >= 2 else (-0.5, 0.5)
            targets.append(float(lo + (hi - lo) * (0.5 + 0.5 * math.sin(phase * math.pi * 2 + idx))))
        apply_joint_targets(robot, targets)
        return

    if profile == "joint_motion":
        command = _scenario_command(scenario)
        t = step / 60.0
        targets_map = jump_targets(t) if command == "jump" else command_to_targets(command, t)
        joint_ids = _joint_ids(manifest)
        if joint_ids and hasattr(robot, "get_dofs_position"):
            current = robot.get_dofs_position().tolist()
            target_list = [float(current[i]) if i >= len(joint_ids) else 0.0 for i in range(len(current))]
            for idx, joint_id in enumerate(joint_ids):
                if idx < len(target_list) and joint_id in targets_map:
                    target_list[idx] = float(targets_map[joint_id])
            apply_joint_targets(robot, target_list)
        return

    if profile == "lateral_push" and step == 0:
        force_n = float(scenario.config.get("lateral_force_n", 150.0))
        entity = tracked.get("target") or robot
        if entity is not None:
            apply_lateral_force(entity, (force_n, 0.0, 0.0))
        return


def _scenario_command(scenario: Scenario) -> str:
    if scenario.config.get("command_hint"):
        return str(scenario.config["command_hint"])
    return "stand"


def run_genesis_scenario(
    project_dir: Path,
    manifest: BuildablesPhysicsManifest,
    scenario: Scenario,
    *,
    test_id: str | None = None,
) -> dict:
    genesis_runtime.assert_available()
    profile = profile_for_run(scenario, test_id)
    base_mode = str(scenario.config.get("base_mode") or default_base_mode_for_profile(profile))
    payload_kg = float(scenario.config.get("payload_kg", 0.0))
    dt = 1.0 / 60.0
    steps = max(30, int(max(0.5, scenario.duration_s) / dt))
    if profile in {"lateral_push", "plane_and_box_drop"}:
        steps = max(steps, 180)
    if profile == "payload_load":
        steps = max(steps, 240)

    run_id = f"run-{uuid4().hex[:10]}"
    run_dir = project_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC)

    runtime = shared_runtime()
    scene = None
    state_timeseries: list[dict] = []
    step_count = 0
    robot_desc_type: str | None = None
    joint_ids = _joint_ids(manifest)

    with genesis_lock():
        try:
            scene, tracked, robot_desc_type = _build_scene_for_project(
                runtime, manifest, project_dir, base_mode=base_mode, profile=profile, payload_kg=payload_kg
            )
            runtime.build_scene(scene)
            for step in range(steps):
                _apply_profile_pre_step(profile, step, steps, tracked, scenario, manifest)
                scene.step()
                step_count += 1
                state_timeseries.append(build_frame(step, dt, tracked, joint_ids=joint_ids))
        finally:
            if scene is not None and hasattr(scene, "destroy"):
                try:
                    scene.destroy()
                except Exception:
                    pass

    metrics, sources = collect_metrics(manifest, state_timeseries, scenario.id, payload_kg=payload_kg)
    if profile == "lateral_push":
        metrics["applied_force_n"] = float(scenario.config.get("lateral_force_n", 150.0))
        sources["applied_force_n"] = "genesis_state"
    if profile == "payload_load":
        metrics["payload_mass_kg"] = payload_kg
        sources["payload_mass_kg"] = "derived_from_scenario_config"
    status = evaluate_status(scenario.id, metrics, scenario.config)
    ended = datetime.now(UTC)

    logs = [
        "[Genesis] Native scenario executor started.",
        f"[Genesis] profile={profile} base_mode={base_mode}",
        f"[Genesis] scene.build() complete, stepped={step_count}",
        f"[Scenario] {scenario.id} duration={scenario.duration_s:.1f}s",
        f"[Result] {status.upper()}",
    ]

    result = {
        "run_id": run_id,
        "project_id": manifest.project_id,
        "project_mode": manifest.project_mode,
        "scenario_id": scenario.id,
        "test_id": test_id,
        "genesis_profile": profile,
        "base_mode": base_mode,
        "robot_description_type": robot_desc_type or "generated_box",
        "status": status,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "duration_s": (ended - started).total_seconds(),
        "genesis_used": step_count > 0,
        "mocked": False,
        "scene_built": True,
        "manifest_version_used": manifest.version,
        "step_count": step_count,
        "metrics": metrics,
        "metric_sources": sources,
        "events": [{"kind": "genesis_profile", "payload": {"profile": profile, "base_mode": base_mode}}],
        "logs": logs,
        "artifacts": {
            "video_path": None,
            "frames_path": None,
            "urdf_path": manifest.robot_description.urdf_path,
            "mjcf_path": manifest.robot_description.mjcf_path,
        },
        "state_timeseries": state_timeseries,
    }

    (run_dir / "input_manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    (run_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (run_dir / "logs.txt").write_text("\n".join(logs), encoding="utf-8")
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (run_dir / "generated_scene_summary.json").write_text(json.dumps(build_scene_summary(manifest, scenario.config), indent=2), encoding="utf-8")
    (run_dir / "state_timeseries.json").write_text(json.dumps(state_timeseries, indent=2), encoding="utf-8")
    return result


def run_genesis_interactive_segment(
    project_dir: Path,
    manifest: BuildablesPhysicsManifest,
    command: str,
    duration_s: float = 0.35,
    *,
    base_mode: str = "fixed_to_world",
) -> dict:
    genesis_runtime.assert_available()
    dt = 1.0 / 60.0
    steps = max(8, int(duration_s / dt))
    runtime = shared_runtime()
    scene = None
    state_timeseries: list[dict] = []
    step_count = 0
    joint_ids = _joint_ids(manifest)

    with genesis_lock():
        try:
            scene, tracked, _ = _build_scene_for_project(
                runtime,
                manifest,
                project_dir,
                base_mode=base_mode,
                profile="joint_motion",
                payload_kg=0.0,
            )
            runtime.build_scene(scene)
            robot = tracked.get("robot")
            for step in range(steps):
                t = step * dt
                if robot is not None:
                    targets_map = jump_targets(t) if command == "jump" else command_to_targets(command, t)
                    if hasattr(robot, "get_dofs_position"):
                        current = robot.get_dofs_position().tolist()
                        target_list = list(current)
                        for idx, joint_id in enumerate(joint_ids):
                            if idx < len(target_list) and joint_id in targets_map:
                                target_list[idx] = float(targets_map[joint_id])
                        apply_joint_targets(robot, target_list)
                scene.step()
                step_count += 1
                state_timeseries.append(build_frame(step, dt, tracked, joint_ids=joint_ids))
        finally:
            if scene is not None and hasattr(scene, "destroy"):
                try:
                    scene.destroy()
                except Exception:
                    pass

    metrics, _ = collect_metrics(manifest, state_timeseries, "free_drive_segment")
    reached = state_timeseries[-1]["joints"] if state_timeseries else {}
    return {
        "state": state_timeseries[-1] if state_timeseries else {},
        "timeseries": state_timeseries,
        "metrics": metrics,
        "step_count": step_count,
        "genesis_used": step_count > 0,
        "mocked": False,
        "reached_joints": reached,
    }


def list_project_dofs(project_dir: Path, manifest: BuildablesPhysicsManifest) -> dict:
    genesis_runtime.assert_available()
    runtime = shared_runtime()
    scene = None
    with genesis_lock():
        try:
            scene, tracked, robot_desc_type = _build_scene_for_project(
                runtime, manifest, project_dir, base_mode="fixed_to_world", profile="passive_gravity", payload_kg=0.0
            )
            runtime.build_scene(scene)
            robot = tracked.get("robot") or tracked.get("target")
            if robot is None:
                return {"count": 0, "dofs": [], "robot_description_type": robot_desc_type}
            info = list_dofs(robot)
            joint_ids = _joint_ids(manifest)
            dofs = []
            positions = robot.get_dofs_position().tolist() if hasattr(robot, "get_dofs_position") else []
            for idx in range(info["count"]):
                limits = info["limits"][idx] if idx < len(info["limits"]) else [-3.14, 3.14]
                dofs.append(
                    {
                        "index": idx,
                        "joint_id": joint_ids[idx] if idx < len(joint_ids) else f"dof_{idx}",
                        "position": float(positions[idx]) if idx < len(positions) else 0.0,
                        "lower_limit": float(limits[0]) if len(limits) >= 1 else -3.14,
                        "upper_limit": float(limits[1]) if len(limits) >= 2 else 3.14,
                    }
                )
            return {"count": info["count"], "dofs": dofs, "robot_description_type": robot_desc_type}
        finally:
            if scene is not None and hasattr(scene, "destroy"):
                try:
                    scene.destroy()
                except Exception:
                    pass


def apply_joint_command(
    project_dir: Path,
    manifest: BuildablesPhysicsManifest,
    targets: list[float],
    *,
    steps: int = 60,
) -> dict:
    genesis_runtime.assert_available()
    runtime = shared_runtime()
    scene = None
    dt = 1.0 / 60.0
    state_timeseries: list[dict] = []
    step_count = 0
    joint_ids = _joint_ids(manifest)

    with genesis_lock():
        try:
            scene, tracked, robot_desc_type = _build_scene_for_project(
                runtime, manifest, project_dir, base_mode="fixed_to_world", profile="joint_sweep", payload_kg=0.0
            )
            runtime.build_scene(scene)
            robot = tracked.get("robot") or tracked.get("target")
            if robot is None:
                raise RuntimeError("No robot entity available for joint command.")
            apply_joint_targets(robot, targets)
            for step in range(max(1, steps)):
                scene.step()
                step_count += 1
                state_timeseries.append(build_frame(step, dt, tracked, joint_ids=joint_ids))
            reached = robot.get_dofs_position().tolist() if hasattr(robot, "get_dofs_position") else []
            return {
                "genesis_used": step_count > 0,
                "mocked": False,
                "step_count": step_count,
                "targets": targets,
                "reached": [float(v) for v in reached],
                "robot_description_type": robot_desc_type,
                "state_timeseries": state_timeseries,
            }
        finally:
            if scene is not None and hasattr(scene, "destroy"):
                try:
                    scene.destroy()
                except Exception:
                    pass
