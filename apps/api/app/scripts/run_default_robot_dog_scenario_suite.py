from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.project_store import load_manifest, project_dir
from app.services.genesis.scenario_runner import run_scenario_sync
from app.services.genesis.genesis_runtime import genesis_runtime


SCENARIOS = [
    "stand_balance",
    "walk_forward",
    "turn_test",
    "jump_test",
    "slope_climb",
    "step_test",
    "rough_terrain",
    "obstacle_avoidance",
    "payload_carry",
    "joint_sweep_collision",
    "torque_margin",
    "sensor_visibility",
    "wire_route",
    "component_fit",
]


def main() -> int:
    genesis_runtime.assert_available()
    manifest = load_manifest("default-robot-dog")
    project = project_dir("default-robot-dog")
    summary: list[dict] = []
    for scenario_id in SCENARIOS:
        scenario = next((s for s in manifest.scenarios if s.id == scenario_id), None)
        if not scenario:
            continue
        result = run_scenario_sync(project, manifest, scenario)
        summary.append(
            {
                "scenario_id": scenario_id,
                "status": result["status"],
                "step_count": result["step_count"],
                "manifest_version_used": result["manifest_version_used"],
            }
        )
        print(f"{scenario_id}: {result['status']} steps={result['step_count']}")
    out = project / "runs" / "scenario-suite-summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
