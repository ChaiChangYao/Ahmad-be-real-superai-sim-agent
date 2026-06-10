from __future__ import annotations

from typing import Any


def native_viewer_options() -> Any:
    import genesis as gs

    return gs.options.ViewerOptions(
        max_FPS=60,
        refresh_rate=60,
        camera_up=(0.0, 0.0, 1.0),
        camera_pos=(3.5, 0.5, 2.5),
        camera_lookat=(0.0, 0.0, 0.5),
    )
