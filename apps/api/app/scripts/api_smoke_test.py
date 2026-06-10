from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from fastapi.testclient import TestClient

from main import app


def _run_and_get_metric(client: TestClient, project_id: str, scenario_id: str, metric: str) -> float:
    result = client.post(f"/projects/{project_id}/scenarios/{scenario_id}/run")
    payload = result.json()
    return float(payload["metrics"][metric])


def main() -> int:
    client = TestClient(app)
    health = client.get("/health")
    genesis = client.get("/genesis/status")
    print("health", health.status_code)
    print("genesis", genesis.status_code)
    if not genesis.json().get("installed"):
        print("Genesis not installed. API smoke test blocked by setup.")
        return 1

    project_id = "default-robot-dog"
    manifest = client.get(f"/projects/{project_id}/manifest").json()

    battery = next((e for e in manifest["electronics"] if "battery" in e["component_profile_id"].lower()), None)
    battery["transform"]["position"]["z"] = 0.11
    client.put(f"/projects/{project_id}/manifest", json=manifest)
    first_balance = _run_and_get_metric(client, project_id, "stand_balance", "max_pitch_deg")

    battery["transform"]["position"]["z"] = 0.20
    client.put(f"/projects/{project_id}/manifest", json=manifest)
    second_balance = _run_and_get_metric(client, project_id, "stand_balance", "max_pitch_deg")

    payload_scenario = next((s for s in manifest["scenarios"] if s["id"] == "payload_carry"), None)
    payload_scenario["config"]["payload_kg"] = 3.0
    client.put(f"/projects/{project_id}/manifest", json=manifest)
    first_payload = _run_and_get_metric(client, project_id, "payload_carry", "min_torque_margin")

    payload_scenario["config"]["payload_kg"] = 12.0
    client.put(f"/projects/{project_id}/manifest", json=manifest)
    second_payload = _run_and_get_metric(client, project_id, "payload_carry", "min_torque_margin")

    actuator = manifest["actuators"][0]
    actuator["max_torque_nm"] = 0.8
    client.put(f"/projects/{project_id}/manifest", json=manifest)
    first_torque = _run_and_get_metric(client, project_id, "torque_margin", "min_torque_margin")

    actuator["max_torque_nm"] = 2.5
    client.put(f"/projects/{project_id}/manifest", json=manifest)
    second_torque = _run_and_get_metric(client, project_id, "torque_margin", "min_torque_margin")

    changed = (first_balance != second_balance) and (first_payload != second_payload) and (first_torque != second_torque)
    print("balance_changed", first_balance, second_balance)
    print("payload_changed", first_payload, second_payload)
    print("torque_changed", first_torque, second_torque)
    print("PASS" if changed else "FAIL")
    return 0 if changed else 1


if __name__ == "__main__":
    raise SystemExit(main())
