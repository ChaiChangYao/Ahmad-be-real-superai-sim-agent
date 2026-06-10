from __future__ import annotations


def default_robot_arm_pose_targets(t: float) -> dict[str, float]:
    return {
        "arm_shoulder_yaw": 0.35 * min(1.0, t),
        "arm_shoulder_pitch": 0.45 * min(1.0, t),
        "arm_elbow_pitch": -0.75 * min(1.0, t),
        "arm_wrist_roll": 1.2 * min(1.0, t),
        "arm_gripper": 0.3,
    }
