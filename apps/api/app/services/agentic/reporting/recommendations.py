"""Actionable recommendations from report input."""
from __future__ import annotations

from app.services.agentic.buildables_cad_bridge import request_missing_mesh_generation
from app.services.agentic.reporting.schemas import (
    DetectedIssue,
    EngineeringRecommendation,
    ReporterInput,
)
from app.services.agentic.test_requirements import evaluate_all_tests, get_test_spec

_MOTION_TESTS = {"gravity_stability", "joint_sweep"}
_SENSOR_TESTS = {"imu_sensor", "contact_force", "depth_camera", "thermal_grid_readiness"}


def suggest_next_tests(project_id: str, test_id: str, outcome_status: str) -> list[str]:
    readiness = evaluate_all_tests(project_id)
    candidates: list[str] = []
    for row in readiness:
        if row.test_id == test_id:
            continue
        if row.can_run or row.can_run_with_fallback:
            candidates.append(row.test_id)
    if outcome_status in ("failed", "blocked", "warning"):
        if test_id in _MOTION_TESTS and "static_mesh_preview" not in candidates:
            candidates.insert(0, "static_mesh_preview")
    return candidates[:5]


def build_recommendations(inp: ReporterInput, outcome_status: str) -> list[EngineeringRecommendation]:
    recs: list[EngineeringRecommendation] = []
    issue_codes = {i.code for i in inp.log_issues}

    if "missing_asset" in issue_codes or inp.robot_metrics.get("missing_mesh_count", 0) > 0:
        recs.append(
            EngineeringRecommendation(
                recommendation_id="upload_meshes",
                title="Upload missing mesh files",
                description="URDF references meshes that were not found. Upload STL/OBJ files or export from STEP.",
                priority="high",
                next_step_type="upload_file",
                action_id="upload_assets",
            )
        )
        bridge = request_missing_mesh_generation(inp.project_id, [])
        if bridge.status == "not_implemented":
            recs.append(
                EngineeringRecommendation(
                    recommendation_id="cad_bridge_meshes",
                    title="Ask Buildables CAD (not connected)",
                    description=bridge.explanation,
                    priority="low",
                    next_step_type="change_design",
                    action_id="cad_bridge",
                )
            )

    if inp.skeleton_fallback:
        recs.append(
            EngineeringRecommendation(
                recommendation_id="add_meshes",
                title="Add visual meshes for full validation",
                description="Skeleton preview ran without full visuals — upload meshes before claiming visual fidelity.",
                priority="medium",
                next_step_type="upload_file",
                action_id="upload_assets",
            )
        )

    if outcome_status in ("failed", "warning", "inconclusive"):
        recs.append(
            EngineeringRecommendation(
                recommendation_id="rerun",
                title="Re-run after fixing blockers",
                description="Address detected issues, then run the same test again.",
                priority="medium",
                next_step_type="rerun_test",
                action_id="run_simulation",
                test_id=inp.test_id,
            )
        )

    if "missing_dependency" in issue_codes:
        recs.append(
            EngineeringRecommendation(
                recommendation_id="install_deps",
                title="Install missing dependencies",
                description="Check API readiness panel and install optional Genesis/Python packages.",
                priority="high",
                next_step_type="add_metadata",
                action_id="check_dependencies",
            )
        )

    if "cpu_fallback" in issue_codes:
        recs.append(
            EngineeringRecommendation(
                recommendation_id="cpu_note",
                title="CPU execution note",
                description="Run used CPU fallback — expect slower performance, not necessarily incorrect physics.",
                priority="low",
                next_step_type="change_design",
                action_id="",
            )
        )

    next_tests = suggest_next_tests(inp.project_id, inp.test_id, outcome_status)
    for tid in next_tests[:2]:
        spec = get_test_spec(tid)
        recs.append(
            EngineeringRecommendation(
                recommendation_id=f"next_{tid}",
                title=f"Try {spec.display_name if spec else tid}",
                description=spec.description if spec else f"Run follow-up test: {tid}",
                priority="low",
                next_step_type="run_another_test",
                action_id="select_test",
                test_id=tid,
            )
        )

    if not recs:
        recs.append(
            EngineeringRecommendation(
                recommendation_id="explore_tests",
                title="Explore other simulation tests",
                description="Review recommended tests in the assistant for broader coverage.",
                priority="low",
                next_step_type="run_another_test",
                action_id="run_preflight",
            )
        )
    return recs


def issues_to_observed_strings(issues: list[DetectedIssue]) -> list[str]:
    return [f"{i.title}: {i.explanation}" for i in issues]
