from __future__ import annotations

from app.services.controls.robot_dog_controller import command_to_targets


def remote_control_targets(command: str, t: float) -> dict[str, float]:
    return command_to_targets(command, t)
