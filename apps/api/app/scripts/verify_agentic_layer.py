"""Verification script for Agentic Simulation Layer Part 1."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "apps" / "api"))

from app.services.agentic.dependencies import check_dependency_status, get_optional_feature_status
from app.services.agentic.file_inventory import scan_project_assets
from app.services.agentic.planner import create_simulation_plan
from app.services.agentic.test_requirements import evaluate_test_readiness, get_all_test_specs
from app.services.agentic.urdf_inspector import inspect_all_robot_descriptions
from app.services.project_store import project_dir


def _find_project_with_urdf() -> str | None:
    root = REPO / "sim-data" / "projects"
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        imported = child / "assets" / "imported"
        if imported.is_dir() and list(imported.rglob("*.urdf")):
            return child.name
    return None


def _case_header(n: int, title: str) -> None:
    print(f"\n=== Case {n}: {title} ===")


def main() -> int:
    results: list[dict] = []
    print("Dependencies:", json.dumps(check_dependency_status(), indent=2))
    print("Features:", json.dumps(get_optional_feature_status(), indent=2))

    specs = get_all_test_specs()
    assert len(specs) >= 8, f"Expected at least 8 test specs, got {len(specs)}"
    print(f"\nTest matrix: {len(specs)} specs OK")

    # Case 2: Full mesh project (imported with resolved meshes)
    full_project = "imported-85653eba" if (REPO / "sim-data" / "projects" / "imported-85653eba").is_dir() else _find_project_with_urdf()
    if full_project:
        _case_header(2, "URDF + full meshes")
        scan_project_assets(full_project)
        descs = inspect_all_robot_descriptions(full_project)
        missing = sum(1 for d in descs for m in d.mesh_references if m.status == "missing")
        plan = create_simulation_plan(full_project, "gravity test joint sweep")
        print(f"  project={full_project}")
        print(f"  missing_meshes={missing}")
        print(f"  recommended={[t.test_id for t in plan.recommended_tests if t.can_run or t.can_run_with_fallback]}")
        results.append({"case": 2, "missing": missing, "ok": missing == 0})

    # Case 4: IMU on robot without sensor metadata
    if full_project:
        _case_header(4, "IMU test without sensor metadata")
        imu = evaluate_test_readiness(full_project, "imu_sensor")
        plan = create_simulation_plan(full_project, "run IMU test")
        print(f"  imu can_run={imu.can_run} fallback={imu.can_run_with_fallback}")
        print(f"  questions={imu.required_user_questions}")
        results.append({"case": 4, "imu_ok": imu.can_run or imu.can_run_with_fallback})

    # Case 5: CFD readiness
    if full_project:
        _case_header(5, "CFD readiness")
        cfd = evaluate_test_readiness(full_project, "cfd_readiness")
        print(f"  can_run={cfd.can_run} blockers={cfd.blockers[:2]}")
        results.append({"case": 5, "cfd_blocked": not cfd.can_run})

    # Case 1 & 3: synthetic temp projects
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        fake_id = "verify-agentic-temp"
        proj = tmp_path / "projects" / fake_id
        imported = proj / "assets" / "imported"
        imported.mkdir(parents=True)

        # Case 1: URDF + STEP, no meshes
        _case_header(1, "URDF + STEP, missing STLs")
        urdf_src = REPO / "sim-data" / "projects" / "imported-85653eba" / "assets" / "imported" / "robot_dog_buildables_demo.urdf"
        step_src = REPO / "sim-data" / "projects" / "imported-85653eba" / "assets" / "imported" / "robot_dog_buildables_demo" / "robot_dog_buildables_demo.step"
        if not step_src.is_file():
            step_src = REPO / "sim-data" / "projects" / "default-robot-dog" / "assets" / "imported" / "robot_dog_buildables_demo.step"
        if urdf_src.is_file():
            shutil.copy2(urdf_src, imported / "robot.urdf")
        if step_src.is_file():
            shutil.copy2(step_src, imported / "model.step")

        import app.paths as paths_mod
        import app.services.project_store as ps_mod

        orig_projects = paths_mod.projects_root
        orig_ps = ps_mod.projects_root
        paths_mod.projects_root = lambda: tmp_path / "projects"  # type: ignore
        ps_mod.projects_root = lambda: tmp_path / "projects"  # type: ignore

        try:
            scan_project_assets(fake_id)
            descs = inspect_all_robot_descriptions(fake_id)
            missing = sum(1 for d in descs for m in d.mesh_references if m.status == "missing")
            plan = create_simulation_plan(fake_id, "joint sweep")
            print(f"  missing_meshes={missing}")
            print(f"  blocked={[t.test_id for t in plan.blocked_tests[:3]]}")
            print(f"  generation_tasks={plan.generation_tasks[:3]}")
            results.append({"case": 1, "missing_gt_0": missing > 0})

            # Case 3: STEP only
            _case_header(3, "STEP only")
            shutil.rmtree(imported)
            imported.mkdir()
            if step_src.is_file():
                shutil.copy2(step_src, imported / "only.step")
            scan_project_assets(fake_id)
            plan3 = create_simulation_plan(fake_id, "robot walk")
            print(f"  recommended={[t.test_id for t in plan3.recommended_tests]}")
            print(f"  fea_blocked=any")
            fea = evaluate_test_readiness(fake_id, "fea_readiness")
            print(f"  fea can_run={fea.can_run}")
            results.append({"case": 3, "no_robot_blocked": not any(t.can_run for t in plan3.recommended_tests if t.test_id == "joint_sweep")})
        finally:
            paths_mod.projects_root = orig_projects  # type: ignore
            ps_mod.projects_root = orig_ps  # type: ignore

    print("\n=== Summary ===")
    for r in results:
        print(r)
    print("\nVerification complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
