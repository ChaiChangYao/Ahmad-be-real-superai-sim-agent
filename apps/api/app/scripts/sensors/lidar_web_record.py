"""Headless LiDAR arena demo for Buildables web replay (no teleop / infinite loop)."""
from __future__ import annotations

import argparse
import math
import os

import numpy as np

import genesis as gs
from genesis.utils.geom import euler_to_quat

NUM_CYLINDERS = 8
NUM_BOXES = 6
CYLINDER_RING_RADIUS = 3.0
BOX_RING_RADIUS = 5.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Buildables web LiDAR recording demo")
    parser.add_argument("--cpu", action="store_true", help="Run on CPU instead of GPU")
    parser.add_argument("--steps", type=int, default=301, help="Simulation steps to record")
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu, precision="32", logging_level="info")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            gravity=(0.0, 0.0, -1.0),
            dt=0.01,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(-6.0, 0.0, 4.0),
            camera_lookat=(0.0, 0.0, 0.5),
            max_FPS=60,
        ),
        profiling_options=gs.options.ProfilingOptions(show_FPS=False),
        show_viewer=False,
    )

    scene.add_entity(gs.morphs.Plane())

    for i in range(NUM_CYLINDERS):
        angle = 2 * math.pi * i / NUM_CYLINDERS
        x = CYLINDER_RING_RADIUS * math.cos(angle)
        y = CYLINDER_RING_RADIUS * math.sin(angle)
        scene.add_entity(
            gs.morphs.Cylinder(
                height=1.5,
                radius=0.3,
                pos=(x, y, 0.75),
                fixed=True,
            )
        )

    for i in range(NUM_BOXES):
        angle = 2 * math.pi * i / NUM_BOXES + math.pi / 6
        x = BOX_RING_RADIUS * math.cos(angle)
        y = BOX_RING_RADIUS * math.sin(angle)
        scene.add_entity(
            gs.morphs.Box(
                size=(0.5, 0.5, 2.0 * (i + 1) / NUM_BOXES),
                pos=(x, y, 1.0),
                fixed=False,
            )
        )

    robot = scene.add_entity(
        gs.morphs.URDF(
            file="urdf/go2/urdf/go2.urdf",
            pos=(0.0, 0.0, 0.35),
            quat=(1.0, 0.0, 0.0, 0.0),
            fixed=True,
        )
    )

    scene.add_sensor(
        gs.sensors.Lidar(
            pattern=gs.sensors.SphericalPattern(),
            entity_idx=robot.idx,
            pos_offset=(0.3, 0.0, 0.1),
            euler_offset=(0.0, 0.0, 0.0),
            return_world_frame=True,
            draw_debug=True,
        )
    )

    scene.build()

    init_pos = np.array([0.0, 0.0, 0.35], dtype=np.float32)
    init_euler = np.array([0.0, 0.0, 0.0], dtype=np.float32)

    steps = 5 if "PYTEST_VERSION" in os.environ else max(1, args.steps)
    print(f"[lidar_web_record] Recording {steps} steps (headless)", flush=True)

    for step in range(steps):
        yaw = 0.35 * math.sin(step * 0.04)
        euler = init_euler.copy()
        euler[2] = yaw
        robot.set_pos(init_pos)
        robot.set_quat(euler_to_quat(euler))
        scene.step()
        if step % 50 == 0:
            print(f"[lidar_web_record] step {step}/{steps}", flush=True)

    print("[lidar_web_record] Done.", flush=True)


if __name__ == "__main__":
    main()
