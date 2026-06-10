"""Minimal Genesis viewer test — plane only. Run from terminal, not by double-clicking."""
from __future__ import annotations

import sys
import traceback

import genesis as gs


def main() -> int:
    try:
        gs.init()
        scene = gs.Scene(
            show_viewer=True,
            vis_options=gs.options.VisOptions(shadow=False),
            viewer_options=gs.options.ViewerOptions(
                camera_pos=(3.5, 0.5, 2.5),
                camera_lookat=(0.0, 0.0, 0.0),
                max_FPS=60,
            ),
        )
        scene.add_entity(gs.morphs.Plane())
        scene.build()
        print("Viewer built successfully. Stepping simulation — close the window or Ctrl+C to exit.")
        while True:
            scene.step()
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0
    except Exception:
        traceback.print_exc()
        input("Minimal viewer test failed. Press Enter to exit...")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
