from app.services.project_store import load_manifest, project_dir
from app.services.genesis.scenario_runner import run_scenario_sync


def main() -> int:
    project_id = "robot-dog-demo"
    manifest = load_manifest(project_id)
    scenario = manifest.scenarios[0]
    result = run_scenario_sync(project_dir(project_id), manifest, scenario)
    print(result["run_id"], result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
