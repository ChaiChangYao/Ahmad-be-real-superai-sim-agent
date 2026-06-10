from __future__ import annotations


KEY_TO_COMMAND = {
    "w": "forward",
    "s": "backward",
    "a": "left",
    "d": "right",
    " ": "jump",
    "r": "reset",
    "escape": "emergency_stop",
}


def map_key_to_command(key: str) -> str | None:
    return KEY_TO_COMMAND.get(key.lower())
