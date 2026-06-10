"""Run an upstream genesis-world example with optional headless patch (no pyrender window)."""
from __future__ import annotations

import argparse
import os
import runpy
import sys
import traceback
from pathlib import Path

_RECORDER: dict | None = None


def _install_headless_patch() -> None:
    import genesis as gs

    original_init = gs.Scene.__init__

    def patched_init(self, *args, **kwargs):
        kwargs["show_viewer"] = False
        return original_init(self, *args, **kwargs)

    gs.Scene.__init__ = patched_init  # type: ignore[method-assign]


def _install_viewer_compat() -> None:
    """Patch upstream scripts for AMD OpenGL (shadow FBO fails)."""
    import genesis as gs

    from app.services.genesis_native.viewer_options import native_viewer_options

    if getattr(gs.Scene.__init__, "_buildables_viewer_compat", False):
        return

    original_init = gs.Scene.__init__

    def patched_init(self, *args, **kwargs):
        if kwargs.get("show_viewer", False):
            vis = kwargs.get("vis_options")
            if vis is None:
                kwargs["vis_options"] = gs.options.VisOptions(shadow=False, plane_reflection=False)
            elif hasattr(vis, "model_copy"):
                kwargs["vis_options"] = vis.model_copy(update={"shadow": False, "plane_reflection": False})
            if kwargs.get("viewer_options") is None:
                kwargs["viewer_options"] = native_viewer_options()
        return original_init(self, *args, **kwargs)

    patched_init._buildables_viewer_compat = True  # type: ignore[attr-defined]
    gs.Scene.__init__ = patched_init  # type: ignore[method-assign]


def _install_web_recorder(record_path: Path, script_path: str) -> None:
    from app.services.genesis_showcase.scene_replay_exporter import install_scene_recorder
    from app.services.genesis_showcase.showcase_script_catalog import infer_demo_type_from_script

    global _RECORDER
    demo_type = os.environ.get("BUILDABLES_DEMO_TYPE") or infer_demo_type_from_script(script_path)
    _RECORDER = install_scene_recorder(record_path, script_path=script_path, demo_type=demo_type)


def main() -> int:
    parser = argparse.ArgumentParser(description="Buildables showcase subprocess launcher")
    parser.add_argument("--script", required=True, help="Path to upstream example .py")
    parser.add_argument("--headless", action="store_true", help="Force show_viewer=False")
    parser.add_argument("--record-web", action="store_true", help="Record state_timeseries.json for web replay")
    parser.add_argument("script_args", nargs=argparse.REMAINDER, help="Args forwarded to the script (prefix with --)")
    args = parser.parse_args()

    script_path = os.path.abspath(args.script)
    if not os.path.isfile(script_path):
        print(f"[showcase_launcher] Script not found: {script_path}", file=sys.stderr)
        return 1

    record_path = os.environ.get("BUILDABLES_RECORD_PATH")
    print(f"[showcase_launcher] Running script: {script_path}", flush=True)
    print(f"[showcase_launcher] Headless: {args.headless} · Web record: {args.record_web}", flush=True)
    if record_path:
        print(f"[showcase_launcher] Record path: {record_path}", flush=True)

    if args.headless:
        os.environ["BUILDABLES_HEADLESS"] = "1"
        os.environ.setdefault("BUILDABLES_WEB_RECORD", "1")
        os.environ["MPLBACKEND"] = "Agg"
        os.environ["BUILDABLES_DISABLE_NATIVE_PLOTS"] = "1"
        from app.services.genesis_showcase.telemetry_recorder import install_headless_plot_hooks

        install_headless_plot_hooks()
        _install_headless_patch()
    else:
        _install_viewer_compat()

    if args.record_web and not args.headless:
        print(
            "[showcase_launcher] ERROR: --record-web with native viewer is unsupported; skipping recorder",
            file=sys.stderr,
            flush=True,
        )
    elif args.record_web and record_path:
        _install_web_recorder(Path(record_path), script_path)

    forwarded = list(args.script_args)
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]
    if args.headless and "--no-vis" not in forwarded and "-nv" not in forwarded:
        try:
            from app.services.genesis_showcase.example_script_runner import _script_accepts_no_vis

            if _script_accepts_no_vis(Path(script_path)):
                forwarded = ["--no-vis", *forwarded]
        except Exception:
            pass
    print(f"[showcase_launcher] Forwarded args: {forwarded or '(none)'}", flush=True)
    sys.argv = [script_path, *forwarded]

    try:
        runpy.run_path(script_path, run_name="__main__")
        print("[showcase_launcher] Demo finished.", flush=True)
        if _RECORDER is not None:
            _RECORDER["flush"](partial=False)
        return 0
    except Exception:
        print("[showcase_launcher] Demo crashed:", file=sys.stderr, flush=True)
        traceback.print_exc()
        if _RECORDER is not None:
            _RECORDER["flush"](partial=False)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
