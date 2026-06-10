from __future__ import annotations



from pathlib import Path

import json

import sys



ROOT = Path(__file__).resolve().parents[3]

API_ROOT = ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:

    sys.path.insert(0, str(API_ROOT))



from app.models.manifest import Scenario

from app.services.genesis.genesis_runtime import genesis_runtime

from app.services.genesis.scenario_runner import run_scenario_sync

from app.services.project_store import load_manifest, project_dir, save_manifest

from app.services.genesis.demo_project_setup import ensure_default_robot_dog_ready





def main() -> int:

    genesis_runtime.assert_available()

    project_id = "default-robot-dog"

    pdir = project_dir(project_id)

    manifest = load_manifest(project_id)

    if ensure_default_robot_dog_ready(manifest, pdir):

        save_manifest(project_id, manifest)



    scenario = Scenario(

        id="smoke-test",

        name="Robot Dog Genesis Smoke Test",

        description="Genesis runtime smoke test with stand + motion profile",

        duration_s=2.5,

        config={"genesis_profile": "joint_motion", "command_hint": "stand"},

    )

    result = run_scenario_sync(pdir, manifest, scenario, test_id="smoke-test")



    smoke_dir = pdir / "runs" / "smoke-test"

    smoke_dir.mkdir(parents=True, exist_ok=True)

    (smoke_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    (smoke_dir / "logs.txt").write_text("\n".join(result["logs"]), encoding="utf-8")

    (smoke_dir / "state_timeseries.json").write_text(json.dumps(result["state_timeseries"], indent=2), encoding="utf-8")



    assert result.get("genesis_used") is True, "genesis_used must be true"

    assert result.get("mocked") is False, "mocked must be false"

    assert result.get("step_count", 0) > 0, "step_count must be > 0"



    print("=== Robot Dog Genesis Smoke Test ===")

    print(f"project_id={project_id}")

    print(f"run_id={result['run_id']}")

    print(f"status={result['status']}")

    print(f"steps={result['step_count']}")

    print(f"manifest_version_used={result.get('manifest_version_used')}")

    print(f"robot_description_type={result.get('robot_description_type')}")

    print(f"result_file={smoke_dir / 'result.json'}")

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

