from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.models.manifest import Scenario
from app.services.genesis.genesis_runtime import genesis_runtime
from app.services.genesis_native.scenario_executor import run_genesis_scenario
from app.services.project_store import load_manifest, project_dir


def _assert_run(label: str, result: dict) -> None:
    assert result.get("genesis_used") is True, f"{label}: genesis_used must be true"
    assert result.get("mocked") is False, f"{label}: mocked must be false"
    assert int(result.get("step_count", 0)) > 0, f"{label}: step_count must be > 0"
    series = result.get("state_timeseries") or []
    assert len(series) > 0, f"{label}: state_timeseries missing"
    first = series[0]
    assert "entities" in first or "links" in first, f"{label}: invalid state frame"


def main() -> int:
    genesis_runtime.assert_available()
    failures: list[str] = []

    def run_case(label: str, project_id: str, scenario: Scenario, test_id: str | None = None) -> None:
        try:
            manifest = load_manifest(project_id)
            result = run_genesis_scenario(project_dir(project_id), manifest, scenario, test_id=test_id)
            _assert_run(label, result)
            out_dir = ROOT / "sim-data" / "runs" / "verify_true_genesis"
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f"{label.replace(' ', '_')}.json").write_text(json.dumps({"run_id": result["run_id"], "step_count": result["step_count"]}, indent=2), encoding="utf-8")
            print(f"PASS {label}: steps={result['step_count']} run_id={result['run_id']}")
        except Exception as exc:
            failures.append(f"{label}: {exc}")
            print(f"FAIL {label}: {exc}")

    run_case(
        "plane_and_box_drop",
        "default-robot-dog",
        Scenario(id="verify_box_drop", name="Verify Box Drop", description="Genesis box drop", duration_s=2.0, config={"genesis_profile": "plane_and_box_drop"}),
        test_id="plane_and_box_drop",
    )
    run_case(
        "lateral_push_topple",
        "default-robot-dog",
        Scenario(id="verify_lateral_push", name="Verify Lateral Push", description="Genesis lateral push", duration_s=3.0, config={"genesis_profile": "lateral_push", "lateral_force_n": 180.0}),
        test_id="lateral_push_topple",
    )
    run_case(
        "payload_load",
        "default-robot-dog",
        Scenario(id="verify_payload", name="Verify Payload", description="Genesis payload load", duration_s=3.0, config={"genesis_profile": "payload_load", "payload_kg": 10.0, "base_mode": "free_floating"}),
        test_id="payload_failure",
    )
    run_case(
        "passive_gravity_default",
        "default-robot-dog",
        Scenario(id="verify_passive", name="Verify Passive Gravity", description="Genesis passive gravity", duration_s=2.5, config={"genesis_profile": "passive_gravity", "base_mode": "free_floating"}),
        test_id="free_base_passive_gravity",
    )
    run_case(
        "fixed_base_no_topple",
        "default-robot-dog",
        Scenario(id="verify_fixed", name="Verify Fixed Base", description="Genesis fixed base", duration_s=2.0, config={"genesis_profile": "fixed_base_passive", "base_mode": "fixed_to_world"}),
        test_id="fixed_base_no_topple",
    )

    imported = project_dir("imported-fc2edda5")
    if imported.exists():
        run_case(
            "passive_gravity_imported_urdf",
            "imported-fc2edda5",
            Scenario(id="verify_imported", name="Verify Imported URDF", description="Imported passive gravity", duration_s=2.5, config={"genesis_profile": "passive_gravity", "base_mode": "free_floating"}),
            test_id="passive-gravity",
        )

    if failures:
        print("\nVerification FAILED:")
        for item in failures:
            print(f" - {item}")
        return 1

    print("\nAll true Genesis pipeline checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
