from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
from importlib import metadata
from typing import Any

from app.models.manifest import BuildablesPhysicsManifest


WINDOWS_SETUP_HINT = (
    "Genesis World is not available. See docs/GENESIS_SETUP_WINDOWS.md for Python, PyTorch, and genesis-world setup steps."
)


@dataclass
class GenesisStatus:
    installed: bool
    version: str | None
    backend: str | None
    device: str | None
    error: str | None
    setup_instructions: str


class GenesisRuntime:
    def __init__(self) -> None:
        self._gs: Any = None
        self._import_error: str | None = None
        self._initialized = False
        self._status = self._detect_status()

    def _detect_status(self) -> GenesisStatus:
        try:
            import genesis as gs  # type: ignore

            self._gs = gs
            version = None
            try:
                version = metadata.version("genesis-world")
            except metadata.PackageNotFoundError:
                version = getattr(gs, "__version__", "unknown")
            return GenesisStatus(
                installed=True,
                version=version,
                backend="genesis",
                device="auto",
                error=None,
                setup_instructions=WINDOWS_SETUP_HINT,
            )
        except Exception as exc:
            self._import_error = str(exc)
            return GenesisStatus(
                installed=False,
                version=None,
                backend=None,
                device=None,
                error=str(exc),
                setup_instructions=WINDOWS_SETUP_HINT,
            )

    def status(self) -> GenesisStatus:
        return self._status

    def assert_available(self) -> None:
        if not self._status.installed:
            raise RuntimeError(f"Genesis unavailable: {self._status.error}. {self._status.setup_instructions}")

    def initialize(self) -> None:
        self.assert_available()
        if self._initialized:
            return
        if hasattr(self._gs, "init"):
            self._gs.init()
        self._initialized = True

    def create_scene(self, dt: float = 1.0 / 60.0) -> Any:
        self.initialize()
        if not hasattr(self._gs, "Scene"):
            raise RuntimeError("Genesis Scene API is unavailable in installed package.")
        scene_ctor = self._gs.Scene
        scene = None
        ctor_attempts = [
            {"sim_options": {"dt": dt}, "show_viewer": False},
            {"show_viewer": False},
            {},
        ]
        last_error: Exception | None = None
        for kwargs in ctor_attempts:
            try:
                scene = scene_ctor(**kwargs)
                break
            except Exception as exc:  # noqa: PERF203
                last_error = exc
        if scene is None:
            raise RuntimeError(f"Failed to create Genesis scene: {last_error}")
        self._add_ground(scene)
        self._build_scene(scene)
        return scene

    def _add_ground(self, scene: Any) -> None:
        # Try a few common APIs across Genesis versions.
        if hasattr(scene, "add_ground"):
            scene.add_ground()
            return
        if hasattr(scene, "add_entity") and hasattr(self._gs, "morphs"):
            try:
                plane_ctor = getattr(self._gs.morphs, "Plane", None)
                if plane_ctor:
                    scene.add_entity(plane_ctor())
                    return
            except Exception:
                pass

    def _build_scene(self, scene: Any) -> None:
        if hasattr(scene, "build"):
            scene.build()
            return
        if hasattr(scene, "initialize"):
            scene.initialize()

    def step_scene(self, scene: Any, steps: int) -> int:
        if not hasattr(scene, "step"):
            raise RuntimeError("Genesis scene does not expose step().")
        stepped = 0
        for _ in range(max(1, steps)):
            scene.step()
            stepped += 1
        return stepped

    def teardown_scene(self, scene: Any) -> None:
        for method in ["destroy", "close", "reset"]:
            if hasattr(scene, method):
                try:
                    getattr(scene, method)()
                    return
                except Exception:
                    continue

    def run_smoke_loop(self, manifest: BuildablesPhysicsManifest, steps: int = 180) -> dict:
        scene = self.create_scene()
        started = datetime.now(UTC)
        try:
            stepped = self.step_scene(scene, steps)
            return {
                "project_id": manifest.project_id,
                "steps": stepped,
                "started_at": started.isoformat(),
                "ended_at": datetime.now(UTC).isoformat(),
            }
        finally:
            self.teardown_scene(scene)


genesis_runtime = GenesisRuntime()
