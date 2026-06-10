#!/usr/bin/env python3
"""Verify natural-language goal parsing maps to expected test IDs."""
from __future__ import annotations

import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(API_DIR))

from app.services.agentic.goal_parser import parse_user_goal  # noqa: E402


CASES = [
    ("testing the joint of this robot", ["joint_sweep"]),
    ("test movement", ["joint_sweep"]),
    ("can do a demo to see if it works", ["joint_sweep", "gravity_stability"]),
    ("test gravity", ["gravity_stability"]),
    ("run imu", ["imu_sensor"]),
    ("contact force", ["contact_force"]),
]


def main() -> int:
    failed = 0
    for text, expected in CASES:
        result = parse_user_goal(text)
        got = result.candidate_tests
        missing = [t for t in expected if t not in got]
        if missing:
            print(f"FAIL: {text!r} expected {expected}, got {got}")
            failed += 1
        else:
            print(f"OK: {text!r} -> {got}")
    if failed:
        print(f"\n{failed} goal parser case(s) failed")
        return 1
    print("\nAll goal parser cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
