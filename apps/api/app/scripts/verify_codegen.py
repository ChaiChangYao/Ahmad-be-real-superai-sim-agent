#!/usr/bin/env python3
"""Part 3 codegen verification — ten acceptance cases."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.services.agentic.codegen.generator import generate_genesis_script  # noqa: E402

BANNED = ("franka", "panda", "go2", "plt.show", "cv2.imshow", "subprocess")


def _assert_no_hardcoding(source: str, case: str) -> None:
    lower = source.lower()
    for token in BANNED:
        if token in lower:
            raise AssertionError(f"{case}: banned token '{token}' in generated script")


def _case_step_only_blocked() -> dict:
    """Ephemeral project with STEP only — joint_sweep must fail."""
    import json
    import shutil

    pid = "verify-step-only"
    pdir = ROOT / "sim-data" / "projects" / pid
    if pdir.is_dir():
        shutil.rmtree(pdir)
    assets = pdir / "assets" / "imported"
    assets.mkdir(parents=True)
    step_src = ROOT / "sim-data" / "projects" / "default-robot-dog" / "assets" / "imported" / "robot_dog_buildables_demo.step"
    if step_src.is_file():
        shutil.copy(step_src, assets / "demo.step")
    (pdir / "manifest.buildables.physics.json").write_text(
        json.dumps({"project_id": pid, "name": "STEP Only Verify", "version": 1}, indent=2),
        encoding="utf-8",
    )
    return run_case("case4", pid, "joint_sweep")


def _case_static_preview() -> dict:
    import json
    import shutil

    pid = "verify-step-only"
    pdir = ROOT / "sim-data" / "projects" / pid
    if not pdir.is_dir():
        _case_step_only_blocked()
    from app.services.agentic.cad_recovery import attempt_step_static_preview

    attempt_step_static_preview(pid)
    return run_case("case5", pid, "static_mesh_preview")


def run_case(name: str, project_id: str, test_id: str, **kwargs) -> dict:
    print(f"\n=== {name} ===")
    result = generate_genesis_script(project_id, test_id, **kwargs)
    print(f"success={result.success} template={result.template_id}")
    print(f"explanation={result.explanation}")
    if result.validation.warnings:
        print("warnings:", result.validation.warnings[:3])
    if result.validation.errors:
        print("errors:", result.validation.errors[:3])
    if result.script_path and Path(result.script_path).is_file():
        source = Path(result.script_path).read_text(encoding="utf-8")
        _assert_no_hardcoding(source, name)
        print(f"script_lines={len(source.splitlines())}")
    return result.model_dump()


def main() -> int:
    cases: list[tuple[str, callable]] = [
        (
            "Case 1: URDF + missing meshes, joint_sweep skeleton",
            lambda: run_case(
                "case1",
                "default-robot-dog",
                "joint_sweep",
                fallback_mode="skeleton",
            ),
        ),
        (
            "Case 2: URDF + meshes, joint_sweep",
            lambda: run_case("case2", "default-robot-dog", "joint_sweep"),
        ),
        (
            "Case 3: URDF IMU",
            lambda: run_case(
                "case3",
                "default-robot-dog",
                "imu_sensor",
                user_parameters={"attach_link": "base_link", "sample_rate_hz": 60},
            ),
        ),
        (
            "Case 4: STEP-only robot motion blocked",
            lambda: _case_step_only_blocked(),
        ),
        (
            "Case 5: static preview",
            lambda: _case_static_preview(),
        ),
        (
            "Case 6: FEA blocked",
            lambda: run_case("case6", "default-robot-dog", "fea_readiness"),
        ),
        (
            "Case 7: gravity — no IMU telemetry template",
            lambda: run_case("case7", "default-robot-dog", "gravity_stability"),
        ),
        (
            "Case 8: contact force sensor",
            lambda: run_case(
                "case8",
                "default-robot-dog",
                "contact_force",
                user_parameters={"contact_links": ["base_link"]},
            ),
        ),
        (
            "Case 9: depth camera sensor",
            lambda: run_case(
                "case9",
                "default-robot-dog",
                "depth_camera",
                user_parameters={"resolution": [640, 480], "fov": 60.0},
            ),
        ),
        (
            "Case 10: thermal grid readiness",
            lambda: run_case(
                "case10",
                "default-robot-dog",
                "thermal_grid_readiness",
                user_parameters={"grid_resolution": 16},
            ),
        ),
    ]

    passed = 0
    for label, fn in cases:
        try:
            data = fn()
            if label.startswith("Case 10:"):
                assert data.get("success"), "expected success"
                src = Path(data["script_path"]).read_text(encoding="utf-8")
                assert "temperature" in src.lower() or "thermal" in src.lower()
            elif label.startswith("Case 9:"):
                assert data.get("success"), "expected success"
                src = Path(data["script_path"]).read_text(encoding="utf-8")
                assert "depth" in src.lower()
            elif label.startswith("Case 8:"):
                assert data.get("success"), "expected success"
                src = Path(data["script_path"]).read_text(encoding="utf-8")
                assert "contact_force" in src.lower()
            elif label.startswith("Case 7:"):
                assert data.get("success"), "expected success"
                src = Path(data["script_path"]).read_text(encoding="utf-8")
                assert "attach_imu_sensor" not in src
            elif label.startswith("Case 6:"):
                assert not data.get("success"), "FEA must not generate Genesis script"
            elif label.startswith("Case 5:"):
                if data.get("success"):
                    assert data.get("template_id") == "static_mesh_preview"
            elif label.startswith("Case 4:"):
                assert not data.get("success"), "expected blocked"
            elif label.startswith("Case 3:"):
                assert data.get("success"), "expected success"
                src = Path(data["script_path"]).read_text(encoding="utf-8")
                assert "imu" in src.lower() and "attach_imu_sensor" in src
            elif label.startswith("Case 2:"):
                assert data.get("success"), "expected success"
                assert data.get("template_id") == "joint_sweep"
            elif label.startswith("Case 1:"):
                assert data.get("success"), "expected success"
                assert "skeleton" in (data.get("template_id") or ""), "expected skeleton template"
            passed += 1
            print("PASS")
        except Exception as exc:
            print(f"FAIL: {exc}")

    print(f"\n{passed}/{len(cases)} cases passed")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
