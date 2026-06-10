"""Genesis native viewer compatibility helpers (AMD / integrated GPU OpenGL)."""
from __future__ import annotations

VIEWER_FATAL_MARKERS = (
    "OpenGL",
    "Unable to initialize an OpenGL",
    "GL error",
    "GLError",
    "pyrender",
    "shadow_mapping",
)


def is_viewer_fatal_error(exc: BaseException) -> bool:
    msg = str(exc)
    return any(marker in msg for marker in VIEWER_FATAL_MARKERS)


def viewer_vis_options():
    """Shadow FBO attachment fails on many AMD WGL drivers (OpenGL error 1282)."""
    import genesis as gs

    return gs.options.VisOptions(shadow=False, plane_reflection=False)


def install_upstream_viewer_compat() -> None:
    """Patch gs.Scene so upstream example scripts get viewer-safe VisOptions."""
    import genesis as gs

    if getattr(gs.Scene, "_buildables_viewer_compat", False):
        return

    original_init = gs.Scene.__init__

    def patched_init(self, *args, **kwargs):
        if kwargs.get("show_viewer", False):
            vis = kwargs.get("vis_options")
            if vis is None:
                kwargs["vis_options"] = viewer_vis_options()
            elif hasattr(vis, "model_copy"):
                kwargs["vis_options"] = vis.model_copy(update={"shadow": False, "plane_reflection": False})
        return original_init(self, *args, **kwargs)

    patched_init._buildables_viewer_compat = True  # type: ignore[attr-defined]
    gs.Scene.__init__ = patched_init  # type: ignore[method-assign]
