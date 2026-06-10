from __future__ import annotations

from app.models.manifest import BuildablesPhysicsManifest


def collect_metrics(
    manifest: BuildablesPhysicsManifest,
    state_timeseries: list[dict],
    scenario_id: str,
    payload_kg: float = 0.0,
) -> tuple[dict, dict]:
    if not state_timeseries:
        empty = {
            "body_height_m": 0.0,
            "max_pitch_deg": 0.0,
            "max_roll_deg": 0.0,
            "max_yaw_deg": 0.0,
            "forward_distance_m": 0.0,
            "fall_detected": True,
            "joint_position_ranges": {},
            "foot_contact_ratio": 0.0,
            "collision_count": 0,
            "min_torque_margin": 0.0,
            "center_of_mass": [0.0, 0.0, 0.0],
            "sensor_clearance": 0.0,
            "battery_com_height_m": 0.0,
        }
        return empty, {k: "derived_from_genesis_state" for k in empty.keys()}

    def body_position(frame: dict) -> list[float]:
        if "entities" in frame:
            robot = frame["entities"].get("robot") or frame["entities"].get("target") or {}
            return robot.get("position", [0.0, 0.0, 0.0])
        return frame.get("links", {}).get("body", {}).get("position", [0.0, 0.0, 0.0])

    def pose_value(frame: dict, key: str) -> float:
        if "entities" in frame:
            robot = frame["entities"].get("robot") or frame["entities"].get("target") or {}
            return float(robot.get("pose", {}).get(key, frame.get("pose", {}).get(key, 0.0)))
        return float(frame.get("pose", {}).get(key, 0.0))

    body_series = [body_position(frame) for frame in state_timeseries]
    pitch_series = [pose_value(frame, "pitch_deg") for frame in state_timeseries]
    roll_series = [pose_value(frame, "roll_deg") for frame in state_timeseries]
    yaw_series = [pose_value(frame, "yaw_deg") for frame in state_timeseries]
    contact_series = [frame.get("contacts", {}).get("ratio", 1.0) for frame in state_timeseries]

    first_pos = body_series[0]
    last_pos = body_series[-1]
    body_height = float(last_pos[2])
    max_pitch = max(abs(float(x)) for x in pitch_series)
    max_roll = max(abs(float(x)) for x in roll_series)
    max_yaw = max(abs(float(x)) for x in yaw_series)
    forward_distance = float(last_pos[0] - first_pos[0])
    fall_detected = body_height < 0.16 or max_pitch > 60.0 or max_roll > 60.0

    joint_ranges: dict[str, list[float]] = {}
    for joint in manifest.joints:
        samples = [float(frame.get("joints", {}).get(joint.id, 0.0)) for frame in state_timeseries]
        joint_ranges[joint.id] = [min(samples), max(samples)]

    avg_contact = float(sum(contact_series) / max(1, len(contact_series)))
    battery = next((e for e in manifest.electronics if "battery" in e.component_profile_id.lower()), None)
    battery_z = battery.transform.position.z if battery else 0.0
    avg_torque_cap = sum(a.max_torque_nm for a in manifest.actuators) / max(1, len(manifest.actuators))
    required_torque = max(0.1, 0.25 * payload_kg + 0.45 * (1.0 + max_pitch / 30.0))
    min_torque_margin = avg_torque_cap / required_torque

    metrics = {
        "body_height_m": round(body_height, 4),
        "max_pitch_deg": round(max_pitch, 3),
        "max_roll_deg": round(max_roll, 3),
        "max_yaw_deg": round(max_yaw, 3),
        "forward_distance_m": round(forward_distance, 4),
        "fall_detected": bool(fall_detected),
        "joint_position_ranges": joint_ranges,
        "foot_contact_ratio": round(avg_contact, 4),
        "collision_count": int(sum(frame.get("collisions", 0) for frame in state_timeseries)),
        "min_torque_margin": round(min_torque_margin, 4),
        "center_of_mass": [round(last_pos[0], 4), round(last_pos[1], 4), round(last_pos[2], 4)],
        "sensor_clearance": round(max(0.0, 1.0 - (max_pitch / 90.0)), 4),
        "battery_com_height_m": round(float(battery_z), 4),
    }
    sources = {
        "body_height_m": "genesis_state",
        "max_pitch_deg": "genesis_state",
        "max_roll_deg": "genesis_state",
        "max_yaw_deg": "genesis_state",
        "forward_distance_m": "genesis_state",
        "fall_detected": "derived_from_genesis_state",
        "joint_position_ranges": "genesis_state",
        "foot_contact_ratio": "genesis_state",
        "collision_count": "genesis_state",
        "min_torque_margin": "derived_from_manifest_and_genesis_state",
        "center_of_mass": "derived_from_genesis_state",
        "sensor_clearance": "derived_from_genesis_state",
        "battery_com_height_m": "derived_from_manifest_and_genesis_state",
    }
    return metrics, sources


def evaluate_status(scenario_id: str, metrics: dict, scenario_config: dict) -> str:
    if metrics.get("fall_detected"):
        return "fail"
    if scenario_id == "stand_balance":
        if metrics["max_pitch_deg"] > float(scenario_config.get("pitch_threshold_deg", 12.0)):
            return "fail"
        if metrics["max_roll_deg"] > float(scenario_config.get("roll_threshold_deg", 12.0)):
            return "fail"
        if metrics["body_height_m"] < float(scenario_config.get("height_threshold_m", 0.2)):
            return "fail"
    if scenario_id == "walk_forward" and metrics["forward_distance_m"] < float(scenario_config.get("distance_threshold_m", 0.4)):
        return "fail"
    if scenario_id in {"turn_test", "turn_left", "turn_right"} and metrics["max_yaw_deg"] < float(scenario_config.get("yaw_threshold_deg", 12.0)):
        return "fail"
    if scenario_id == "torque_margin" and metrics["min_torque_margin"] < float(scenario_config.get("required_safety_factor", 1.0)):
        return "fail"
    if scenario_id == "sensor_visibility" and metrics["sensor_clearance"] < float(scenario_config.get("required_clearance_m", 0.1)):
        return "fail"
    if scenario_id == "component_fit" and metrics["collision_count"] > 0:
        return "warning"
    return {
        "free_drive": "pass",
        "free_drive_segment": "pass",
    }.get(scenario_id, "pass")
