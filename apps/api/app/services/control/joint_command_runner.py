from __future__ import annotations


def run_joint_command_table(commands: list[dict]) -> dict:
    return {
        "accepted": True,
        "rows": len(commands),
        "normalized_commands": commands,
    }
