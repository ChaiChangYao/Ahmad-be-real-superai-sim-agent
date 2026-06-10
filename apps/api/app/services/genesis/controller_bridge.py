from __future__ import annotations

from typing import Literal


DriveCommand = Literal["stand", "walk_forward", "walk_backward", "turn_left", "turn_right", "stop", "reset_pose"]


def map_wasd_key(key: str) -> DriveCommand | None:
    key = key.lower()
    if key == "w":
        return "walk_forward"
    if key == "s":
        return "walk_backward"
    if key == "a":
        return "turn_left"
    if key == "d":
        return "turn_right"
    if key == " ":
        return "stop"
    if key == "r":
        return "reset_pose"
    return None
