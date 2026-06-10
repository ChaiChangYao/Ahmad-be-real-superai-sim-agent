"""
Robot dog demo control script.
The host runtime is expected to provide a wrapper API with:
- get_imu()
- get_depth()
- get_contacts()
- get_joint_position(joint_id)
- set_joint_target_position(joint_id, angle_rad)
- set_joint_target_velocity(joint_id, velocity_rad_s)
- set_joint_torque(joint_id, torque_nm)
- emergency_stop()
"""


def stand(api) -> None:
    targets = {
        "j-hip-fl": 0.2,
        "j-knee-fl": -0.7,
        "j-hip-fr": 0.2,
        "j-knee-fr": -0.7,
        "j-hip-rl": 0.2,
        "j-knee-rl": -0.7,
        "j-hip-rr": 0.2,
        "j-knee-rr": -0.7,
    }
    for joint_id, target in targets.items():
        api.set_joint_target_position(joint_id, target)


def walk_forward(api, phase: float) -> None:
    import math
    hip = 0.25 * math.sin(phase)
    knee = -0.6 + 0.2 * math.sin(phase + math.pi / 2)
    api.set_joint_target_position("j-hip-fl", hip)
    api.set_joint_target_position("j-knee-fl", knee)
    api.set_joint_target_position("j-hip-fr", -hip)
    api.set_joint_target_position("j-knee-fr", knee)
    api.set_joint_target_position("j-hip-rl", -hip)
    api.set_joint_target_position("j-knee-rl", knee)
    api.set_joint_target_position("j-hip-rr", hip)
    api.set_joint_target_position("j-knee-rr", knee)
