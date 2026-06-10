from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.project_store import load_manifest, project_dir
from app.services.genesis.genesis_runtime import genesis_runtime
from app.services.genesis.scenario_runner import run_scenario_sync
from app.models.manifest import Scenario


def main() -> int:
    genesis_runtime.assert_available()
    project_id = "default-robot-dog"
    manifest = load_manifest(project_id)
    scenario = Scenario(
        id="smoke-test",
        name="Default Robot Dog Smoke Test",
        description="Genesis runtime smoke test for default-robot-dog",
        duration_s=2.5,
        config={"commands": ["stand", "forward", "left", "stand"]},
    )
    result = run_scenario_sync(project_dir(project_id), manifest, scenario)

    smoke_dir = project_dir(project_id) / "runs" / "smoke-test"
    smoke_dir.mkdir(parents=True, exist_ok=True)
    (smoke_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (smoke_dir / "logs.txt").write_text("\n".join(result["logs"]), encoding="utf-8")
    (smoke_dir / "state_timeseries.json").write_text(json.dumps(result["state_timeseries"], indent=2), encoding="utf-8")

    assert result.get("genesis_used") is True, "genesis_used must be true"
    assert result.get("mocked") is False, "mocked must be false"
    assert result.get("step_count", 0) > 0, "step_count must be > 0"

    print("=== Default Robot Dog Genesis Smoke Test ===")
    print(f"project_id={project_id}")
    print(f"run_id={result['run_id']}")
    print(f"status={result['status']}")
    print(f"steps={result['step_count']}")
    print(f"manifest_version_used={result.get('manifest_version_used')}")
    print(f"result_file={smoke_dir / 'result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
