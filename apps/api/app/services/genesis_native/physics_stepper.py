from __future__ import annotations

from typing import Any


def step(scene: Any, n_steps: int) -> int:
    total = 0
    for _ in range(max(1, n_steps)):
        scene.step()
        total += 1
    return total
