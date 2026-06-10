"""Minimal Genesis demo for web viewer verification: plane + orbiting cube (~5s)."""
from __future__ import annotations

import math

import genesis as gs


def main() -> None:
    gs.init(backend=gs.cpu, precision="32")
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=0.01),
        show_viewer=False,
    )
    scene.add_entity(gs.morphs.Plane())
    cube = scene.add_entity(
        gs.morphs.Box(
            size=(0.18, 0.18, 0.18),
            pos=(0.0, 0.15, 0.3),
        ),
    )
    scene.build()

    # ~5 seconds at dt=0.01 — clear circular motion in the web viewer
    for i in range(500):
        if i % 100 == 0:
            print(f"[minimal_web_viewer_demo] step {i}/500", flush=True)
        t = i * 0.01
        cube.set_pos((0.35 * math.sin(t * 2.5), 0.15, 0.35 * math.cos(t * 2.5)))
        scene.step()


if __name__ == "__main__":
    main()
