"""Run a Genesis viewer script from terminal; keep traceback visible on crash."""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path


def _apply_shadow_off_patch() -> None:
    import genesis as gs

    original_init = gs.Scene.__init__

    def patched_init(self, *args, **kwargs):
        if kwargs.get("show_viewer", False):
            vis = kwargs.get("vis_options")
            if vis is None:
                kwargs["vis_options"] = gs.options.VisOptions(shadow=False, plane_reflection=False)
            elif hasattr(vis, "model_copy"):
                kwargs["vis_options"] = vis.model_copy(update={"shadow": False, "plane_reflection": False})
        return original_init(self, *args, **kwargs)

    gs.Scene.__init__ = patched_init  # type: ignore[method-assign]


def main() -> int:
    parser = argparse.ArgumentParser(description="Debug wrapper for Genesis viewer scripts")
    parser.add_argument("script", type=Path, help="Python script to run (e.g. genesis-world/examples/tutorials/mpm.py)")
    parser.add_argument(
        "--shadow",
        choices=("default", "off"),
        default="off",
        help="VisOptions.shadow override (default: off — required on most AMD GPUs)",
    )
    args = parser.parse_args()

    script = args.script.resolve()
    if not script.is_file():
        print(f"Script not found: {script}", file=sys.stderr)
        return 1

    if args.shadow == "off":
        _apply_shadow_off_patch()
        print(
            "[debug_viewer] Patched gs.Scene: VisOptions(shadow=False) when show_viewer=True "
            "(fixes AMD OpenGL glFramebufferTexture2D error 1282).",
            flush=True,
        )
    else:
        print("[debug_viewer] Using Genesis default shadows (needs NVIDIA-friendly OpenGL).", flush=True)

    try:
        import runpy

        sys.argv = [str(script)]
        runpy.run_path(str(script), run_name="__main__")
        return 0
    except Exception:
        traceback.print_exc()
        print(
            "\n[debug_viewer] If you see _shadow_mapping_pass above, re-run with: --shadow off",
            flush=True,
        )
        input("Viewer crashed. Press Enter to exit...")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
