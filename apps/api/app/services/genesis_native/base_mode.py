from __future__ import annotations

from typing import Literal

BaseMode = Literal["fixed_to_world", "free_floating", "ground_contact", "anchored_mechanism"]


def base_mode_to_fixed(base_mode: str) -> bool:
    if base_mode in {"fixed_to_world", "anchored_mechanism"}:
        return True
    return False


def default_base_mode_for_profile(profile: str) -> BaseMode:
    if profile in {"fixed_base_passive", "joint_sweep", "joint_slider"}:
        return "fixed_to_world"
    if profile in {"passive_gravity", "lateral_push", "payload_load", "free_base_passive"}:
        return "free_floating"
    return "ground_contact"
