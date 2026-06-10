"""Deterministic simulation planner — source of truth before Genesis launch."""
from __future__ import annotations

from app.services.agentic.file_inventory import find_assets_by_role, scan_project_assets
from app.services.agentic.mesh_inspector import inspect_project_meshes
from app.services.agentic.schemas import SimulationPlan, TestReadinessResult
from app.services.agentic.test_requirements import evaluate_all_tests, get_all_test_specs
from app.services.agentic.urdf_inspector import inspect_all_robot_descriptions
from app.services.project_store import project_dir


def _parse_goal_keywords(user_goal: str | None) -> set[str]:
    if not user_goal:
        return set()
    text = user_goal.lower()
    keywords: set[str] = set()
    mapping = {
        "gravity": "gravity_stability",
        "stability": "gravity_stability",
        "balance": "gravity_stability",
        "joint": "joint_sweep",
        "sweep": "joint_sweep",
        "walk": "joint_sweep",
        "motion": "joint_sweep",
        "imu": "imu_sensor",
        "accelerometer": "imu_sensor",
        "gyro": "imu_sensor",
        "contact": "contact_force",
        "force": "contact_force",
        "depth": "depth_camera",
        "camera": "depth_camera",
        "thermal": "thermal_grid_readiness",
        "temperature": "thermal_grid_readiness",
        "heat": "thermal_grid_readiness",
        "fea": "fea_readiness",
        "finite element": "fea_readiness",
        "stress": "fea_readiness",
        "cfd": "cfd_readiness",
        "fluid": "cfd_readiness",
        "aerodynamic": "cfd_readiness",
    }
    for key, test_id in mapping.items():
        if key in text:
            keywords.add(test_id)
    return keywords


def create_simulation_plan(
    project_id: str,
    user_goal: str | None = None,
    candidate_tests: list[str] | None = None,
) -> SimulationPlan:
    """Build a deterministic preflight plan. Does not launch Genesis."""
    if not project_dir(project_id).is_dir():
        return SimulationPlan(
            project_id=project_id,
            user_goal=user_goal,
            warnings=["Project not found."],
            agent_explanation="Project directory does not exist. Import files first.",
        )

    assets = scan_project_assets(project_id)

    robot_descs = inspect_all_robot_descriptions(project_id)
    mesh_inspections = inspect_project_meshes(project_id)
    all_readiness = evaluate_all_tests(project_id)

    if candidate_tests:
        goal_tests_list = list(candidate_tests)
        goal_tests = set(candidate_tests)
    else:
        goal_tests_list = list(_parse_goal_keywords(user_goal))
        goal_tests = set(goal_tests_list)
    recommended: list[TestReadinessResult] = []
    blocked: list[TestReadinessResult] = []

    for result in all_readiness:
        spec = next((s for s in get_all_test_specs() if s.test_id == result.test_id), None)
        is_readiness_only = spec and spec.status == "readiness_only"

        if result.can_run:
            recommended.append(result)
        elif result.can_run_with_fallback and not is_readiness_only:
            recommended.append(result)
        elif is_readiness_only:
            blocked.append(result)
        else:
            blocked.append(result)

    if goal_tests:
        goal_recommended = [r for r in all_readiness if r.test_id in goal_tests and (r.can_run or r.can_run_with_fallback)]
        goal_blocked = [r for r in all_readiness if r.test_id in goal_tests and not r.can_run and not r.can_run_with_fallback]
        if goal_recommended:
            recommended = goal_recommended + [r for r in recommended if r.test_id not in goal_tests]
        if goal_blocked:
            blocked = goal_blocked + [r for r in blocked if r.test_id not in goal_tests]

    urdf_assets = find_assets_by_role(assets, "robot_description")
    mesh_assets = find_assets_by_role(assets, "mesh")
    cad_assets = find_assets_by_role(assets, "cad")
    missing_mesh_count = sum(1 for r in robot_descs for m in r.mesh_references if m.status == "missing")
    total_mesh_refs = sum(len(r.mesh_references) for r in robot_descs)

    asset_summary = {
        "total_assets": len(assets),
        "urdf_count": len(urdf_assets),
        "mesh_count": len(mesh_assets),
        "step_count": len(cad_assets),
        "robot_description_count": len([r for r in robot_descs if r.parsed]),
        "missing_mesh_count": missing_mesh_count,
        "total_mesh_references": total_mesh_refs,
        "mesh_validation_warnings": sum(len(m.warnings) for m in mesh_inspections),
        "mesh_validation_errors": sum(len(m.errors) for m in mesh_inspections),
    }

    plan_steps: list[str] = []
    warnings: list[str] = []
    questions: list[str] = []
    generation_tasks: list[str] = []

    if urdf_assets and cad_assets:
        plan_steps.append("You uploaded a URDF and STEP file(s).")
    elif urdf_assets:
        plan_steps.append("You uploaded a robot description (URDF/MJCF).")
    elif cad_assets:
        plan_steps.append("You uploaded STEP/CAD geometry only (no robot description).")
    elif mesh_assets:
        plan_steps.append("You uploaded mesh files without a robot description.")
    else:
        plan_steps.append("No recognized assets found. Upload URDF, STEP, or mesh files.")

    if total_mesh_refs > 0:
        if missing_mesh_count > 0:
            plan_steps.append(
                f"Your URDF references {total_mesh_refs} mesh file(s), but {missing_mesh_count} are missing.",
            )
            warnings.append("Full visual Genesis launch is blocked until missing meshes are uploaded or generated.")
            generation_tasks.append("recover_missing_meshes_from_step")
        else:
            plan_steps.append(f"All {total_mesh_refs} URDF mesh references are resolved.")

    runnable = [r for r in recommended if r.can_run]
    fallback = [r for r in recommended if r.can_run_with_fallback and not r.can_run]

    if runnable:
        names = ", ".join(r.test_id for r in runnable[:5])
        plan_steps.append(f"Runnable tests: {names}.")
    if fallback:
        names = ", ".join(r.test_id for r in fallback[:5])
        plan_steps.append(f"Tests available with safe defaults/fallback: {names}.")

    for r in blocked:
        if r.test_id in {"fea_readiness", "cfd_readiness"}:
            plan_steps.append(
                f"{r.test_id}: readiness check only — {r.blockers[0] if r.blockers else 'requirements not met'}.",
            )
        elif r.blockers:
            plan_steps.append(f"Blocked: {r.test_id} — {r.blockers[0]}.")

    imu_result = next((r for r in all_readiness if r.test_id == "imu_sensor"), None)
    if imu_result and (imu_result.can_run or imu_result.can_run_with_fallback):
        for q in imu_result.required_user_questions:
            questions.append(q)
            plan_steps.append(q)

    for r in all_readiness:
        generation_tasks.extend(r.generated_defaults_available)
    generation_tasks = list(dict.fromkeys(generation_tasks))

    for r in robot_descs:
        warnings.extend(r.warnings)
    for m in mesh_inspections:
        warnings.extend(m.warnings)

    selected = None
    if goal_tests_list:
        for tid in goal_tests_list:
            match = next((r for r in all_readiness if r.test_id == tid), None)
            if match and (match.can_run or match.can_run_with_fallback):
                selected = tid
                break

    explanation_parts = plan_steps.copy()
    if user_goal:
        explanation_parts.insert(0, f"Goal: {user_goal}")

    return SimulationPlan(
        project_id=project_id,
        user_goal=user_goal,
        asset_summary=asset_summary,
        recommended_tests=recommended,
        blocked_tests=blocked,
        required_questions=list(dict.fromkeys(questions)),
        generation_tasks=generation_tasks,
        selected_test=selected,
        plan_steps=plan_steps,
        warnings=list(dict.fromkeys(warnings)),
        agent_explanation="\n".join(explanation_parts),
    )
