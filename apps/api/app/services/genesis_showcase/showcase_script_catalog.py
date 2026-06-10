from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
import re
from pathlib import Path

from app.paths import repo_root


@dataclass(frozen=True)
class ShowcaseScriptEntry:
    scenario_id: str
    demo_name: str
    layer: str
    script_relpath: str
    repo: str  # "genesis-world" | "genesis-nyx"
    optional_extra: str | None = None  # "nyx" | "pyuipc"
    upstream_url: str = ""
    demo_type: str = "motion"  # motion | telemetry | hybrid
    telemetry_channels: tuple[str, ...] | None = None
    kind: str = "simulation"  # simulation | sensor | gui
    sensor_type: str | None = None


CATALOG_EXCLUDE_IDS: frozenset[str] = frozenset(
    {
        "genesis-simulation-interface-gui-debug-drawing",
        "genesis-simulation-interface-advanced-worm",
        "genesis-simulation-interface-drone",
        "genesis-simulation-interface-gui-mesh-point-picker",
        "genesis-simulation-interface-gui-mouse-interaction",
        "genesis-physics-ipc-robot-cloth-teleop",
        "genesis-rendering-nyx-hello",
        "genesis-rendering-nyx-attached-camera",
        "genesis-rendering-nyx-pbr-materials",
        "genesis-rendering-nyx-light-types",
        "genesis-rendering-nyx-3d-gaussian-splat",
        "genesis-rendering-nyx-object-picking",
        "genesis-rendering-nyx-multi-cam-multi-env",
        "genesis-simulation-interface-sensor-surface-distance",
        "genesis-simulation-interface-sensor-temperature-grid",
    }
)


def infer_demo_type(script_relpath: str, layer: str) -> str:
    rel = script_relpath.replace("\\", "/").lower()
    if "/sensors/" in rel or rel.startswith("examples/sensors/"):
        if any(token in rel for token in ("imu", "lidar", "contact", "tactile", "temperature")):
            return "telemetry"
        return "hybrid"
    if any(token in rel for token in ("depth_camera", "surface_distance")):
        return "hybrid"
    return "motion"


def infer_demo_type_from_script(script_path: str) -> str:
    """Infer demo policy from an absolute or relative upstream script path."""
    return infer_demo_type(script_path, "")


def infer_sensor_type(script_relpath: str, demo_name: str = "") -> str | None:
    rel = script_relpath.replace("\\", "/").lower()
    name = demo_name.lower()
    if "imu" in rel or "imu" in name:
        return "imu"
    if "depth_camera" in rel or "depth camera" in name:
        return "depth_camera"
    if "temperature" in rel or "temperature" in name:
        return "temperature_grid"
    if "contact" in rel or "contact force" in name:
        return "contact_force"
    if "lidar" in rel or "lidar" in name:
        return "lidar"
    if "tactile" in rel or "tactile" in name:
        return "tactile"
    if "surface_distance" in rel or "surface distance" in name:
        return "surface_distance"
    return None


def infer_catalog_kind(script_relpath: str, layer: str = "", demo_name: str = "") -> str:
    rel = script_relpath.replace("\\", "/").lower()
    name = demo_name.strip()
    if name.startswith("GUI:") or "/gui/" in rel or rel.endswith("/imgui_joint_control.py"):
        return "gui"
    if "/sensors/" in rel or rel.startswith("examples/sensors/") or name.startswith("Sensor:"):
        return "sensor"
    if infer_sensor_type(script_relpath, demo_name) is not None:
        return "sensor"
    return "simulation"


def infer_telemetry_channels(script_relpath: str) -> tuple[str, ...] | None:
    rel = script_relpath.replace("\\", "/").lower()
    if "imu" in rel:
        return ("lin_acc", "true_lin_acc", "ang_vel", "true_ang_vel")
    if "lidar" in rel:
        return ("ranges",)
    if "contact" in rel:
        return ("contact_force",)
    if "tactile" in rel:
        return ("tactile",)
    if "temperature" in rel:
        return ("temperature",)
    if "depth_camera" in rel:
        return ("depth",)
    if "surface_distance" in rel:
        return ("distance",)
    return None


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")


def _scenario_id(layer: str, demo_name: str) -> str:
    return f"genesis-{_slug(layer)}-{_slug(demo_name)}"


def _entry(
    layer: str,
    demo_name: str,
    script_relpath: str,
    *,
    repo: str = "genesis-world",
    optional_extra: str | None = None,
    upstream_url: str = "",
    demo_type: str | None = None,
    telemetry_channels: tuple[str, ...] | None = None,
    kind: str | None = None,
    sensor_type: str | None = None,
) -> ShowcaseScriptEntry:
    sid = _scenario_id(layer, demo_name)
    base = "https://github.com/Genesis-Embodied-AI/genesis-nyx" if repo == "genesis-nyx" else "https://github.com/Genesis-Embodied-AI/genesis-world"
    url = upstream_url or f"{base}/blob/main/{script_relpath.replace(chr(92), '/')}"
    resolved_demo_type = demo_type or infer_demo_type(script_relpath, layer)
    resolved_channels = telemetry_channels if telemetry_channels is not None else infer_telemetry_channels(script_relpath)
    resolved_kind = kind or infer_catalog_kind(script_relpath, layer, demo_name)
    resolved_sensor_type = sensor_type if sensor_type is not None else infer_sensor_type(script_relpath, demo_name)
    if resolved_kind != "sensor":
        resolved_sensor_type = None
    return ShowcaseScriptEntry(
        scenario_id=sid,
        demo_name=demo_name,
        layer=layer,
        script_relpath=script_relpath,
        repo=repo,
        optional_extra=optional_extra,
        upstream_url=url,
        demo_type=resolved_demo_type,
        telemetry_channels=resolved_channels,
        kind=resolved_kind,
        sensor_type=resolved_sensor_type,
    )


# Mirrors genesis-world + genesis-nyx catalogue (see genesis-world README).
SHOWCASE_ENTRIES: list[ShowcaseScriptEntry] = [
    _entry(
        "web-viewer",
        "Minimal: cube motion (start here)",
        "apps/api/app/scripts/minimal_web_viewer_demo.py",
        repo="buildables",
        upstream_url="https://github.com/Genesis-Embodied-AI/genesis-world",
    ),
    # Physics
    _entry("physics", "Rigid: franka cube", "examples/rigid/franka_cube.py"),
    _entry("physics", "Rigid: collision tower", "examples/collision/tower.py"),
    _entry("physics", "Rigid: contype", "examples/collision/contype.py"),
    _entry("physics", "FEM: hard & soft constraint", "examples/fem_hard_and_soft_constraint.py"),
    _entry("physics", "MPM: tutorial", "examples/tutorials/mpm.py"),
    _entry("physics", "MPM: sand wheel", "examples/coupling/sand_wheel.py"),
    _entry("physics", "SPH: rigid", "examples/coupling/sph_rigid.py"),
    _entry("physics", "SPH: + MPM", "examples/coupling/sph_mpm.py"),
    _entry("physics", "PBD: liquid", "examples/pbd_liquid.py"),
    _entry("physics", "PBD: cloth", "examples/tutorials/pbd_cloth.py"),
    _entry("physics", "Stable Fluid: smoke", "examples/smoke.py"),
    _entry("physics", "IPC: robot cloth teleop", "examples/IPC_Solver/ipc_robot_cloth_teleop.py", optional_extra="pyuipc"),
    _entry("physics", "Coupler: cloth on rigid", "examples/coupling/cloth_on_rigid.py"),
    _entry("physics", "Coupler: rigid + MPM", "examples/coupling/rigid_mpm_attachment.py"),
    _entry("physics", "Coupler: cut dragon", "examples/coupling/cut_dragon.py"),
    _entry("physics", "Coupler: water wheel", "examples/coupling/water_wheel.py"),
    _entry("physics", "Coupler: flush cubes", "examples/coupling/flush_cubes.py"),
    _entry("physics", "SAP: Franka grasp rigid cube", "examples/sap_coupling/franka_grasp_rigid_cube.py"),
    # Rendering (genesis-world built-in + Nyx plugin)
    _entry("rendering", "Follow entity", "examples/rendering/follow_entity.py"),
    _entry("rendering", "Animated camera", "examples/rendering/moving_camera.py"),
    _entry("rendering", "Nyx: hello", "examples/01_hello_nyx.py", repo="genesis-nyx", optional_extra="nyx"),
    _entry("rendering", "Nyx: attached camera", "examples/02_attached_camera.py", repo="genesis-nyx", optional_extra="nyx"),
    _entry("rendering", "Nyx: PBR materials", "examples/03_materials.py", repo="genesis-nyx", optional_extra="nyx"),
    _entry("rendering", "Nyx: light types", "examples/04_light_types.py", repo="genesis-nyx", optional_extra="nyx"),
    _entry("rendering", "Nyx: 3D Gaussian splat", "examples/05_gaussian_splat.py", repo="genesis-nyx", optional_extra="nyx"),
    _entry("rendering", "Nyx: object picking", "examples/06_object_picking.py", repo="genesis-nyx", optional_extra="nyx"),
    _entry("rendering", "Nyx: multi-cam multi-env", "examples/07_multi_camera_multi_env.py", repo="genesis-nyx", optional_extra="nyx"),
    # Simulation interface
    _entry("simulation-interface", "Controlling a robot", "examples/tutorials/control_your_robot.py"),
    _entry("simulation-interface", "GUI: ImGui joint control", "examples/gui/imgui_joint_control.py"),
    _entry("simulation-interface", "Heterogeneous envs", "examples/rigid/heterogeneous_simulation.py"),
    _entry("simulation-interface", "Domain randomization", "examples/rigid/domain_randomization.py"),
    _entry("simulation-interface", "Sensor: depth camera", "examples/sensors/depth_camera_custom_vverts.py"),
    _entry("simulation-interface", "Sensor: IMU", "examples/sensors/imu_franka.py"),
    _entry(
        "simulation-interface",
        "Sensor: lidar",
        "apps/api/app/scripts/sensors/lidar_web_record.py",
        repo="buildables",
        demo_type="telemetry",
        kind="sensor",
        sensor_type="lidar",
    ),
    _entry("simulation-interface", "Sensor: tactile sandbox", "examples/sensors/tactile_sandbox.py"),
    _entry("simulation-interface", "Sensor: contact force", "examples/sensors/contact_force_go2.py"),
    _entry("simulation-interface", "Sensor: surface distance", "examples/sensors/surface_distance_shadowhand.py"),
    _entry("simulation-interface", "Sensor: temperature grid", "examples/sensors/temperature_grid.py"),
    _entry("simulation-interface", "GUI: debug drawing", "examples/tutorials/draw_debug.py"),
    _entry("simulation-interface", "GUI: mesh point picker", "examples/viewer_plugin/mesh_point_selector.py"),
    _entry("simulation-interface", "GUI: mouse interaction", "examples/viewer_plugin/mouse_interaction.py"),
    _entry("simulation-interface", "Diff-IK controller", "examples/rigid/diffik_controller.py"),
    _entry("simulation-interface", "Batched IK", "examples/tutorials/batched_IK.py"),
    _entry("simulation-interface", "Drone", "examples/drone/hover_train.py"),
    _entry("simulation-interface", "Advanced: worm", "examples/tutorials/advanced_worm.py"),
]

SHOWCASE_BY_ID: dict[str, ShowcaseScriptEntry] = {e.scenario_id: e for e in SHOWCASE_ENTRIES}


def get_showcase_entry(scenario_id: str) -> ShowcaseScriptEntry | None:
    return SHOWCASE_BY_ID.get(scenario_id)


def resolve_repo_root(repo: str) -> Path | None:
    if repo == "genesis-world":
        env = os.getenv("GENESIS_WORLD_ROOT")
        if env:
            root = Path(env).expanduser().resolve()
            if root.exists():
                return root
        try:
            import genesis as gs  # type: ignore

            pkg = Path(gs.__file__).resolve().parent
            for candidate in (pkg.parent, pkg.parent.parent):
                examples = candidate / "examples"
                if examples.is_dir() and (examples / "rigid").is_dir():
                    return candidate
        except Exception:
            pass
        for candidate in (
            repo_root() / "genesis-world",
            Path.home() / "genesis-world",
            Path.cwd() / "genesis-world",
            Path.cwd().parent / "genesis-world",
        ):
            if (candidate / "examples" / "rigid").is_dir():
                return candidate.resolve()
        return None

    if repo == "buildables":
        return repo_root()

    if repo == "genesis-nyx":
        env = os.getenv("GENESIS_NYX_ROOT")
        if env:
            root = Path(env).expanduser().resolve()
            if root.exists():
                return root
        for candidate in (
            repo_root() / "genesis-nyx",
            Path.home() / "genesis-nyx",
            Path.cwd() / "genesis-nyx",
            Path.cwd().parent / "genesis-nyx",
        ):
            if (candidate / "examples" / "01_hello_nyx.py").is_file():
                return candidate.resolve()
        spec = importlib.util.find_spec("gs_nyx")
        if spec and spec.origin:
            pkg = Path(spec.origin).resolve().parent
            examples = pkg.parent / "examples"
            if examples.is_dir():
                return pkg.parent
        return None

    return None


def resolve_script_path(entry: ShowcaseScriptEntry) -> tuple[Path | None, Path | None]:
    root = resolve_repo_root(entry.repo)
    if root is None:
        return None, root
    script = (root / entry.script_relpath).resolve()
    return script if script.is_file() else None, root


def optional_extra_available(extra: str | None) -> tuple[bool, str | None]:
    if extra is None:
        return True, None
    if extra == "nyx":
        if importlib.util.find_spec("gs_nyx") is not None:
            return True, None
        try:
            import importlib.metadata as md

            md.version("gs-nyx-plugin")
            return True, None
        except Exception:
            return False, "Install Nyx: pip install gs-nyx-plugin (CUDA 12.9+, driver 575+). Set GENESIS_NYX_ROOT if examples missing."
    if extra == "pyuipc":
        if importlib.util.find_spec("pyuipc") is not None or importlib.util.find_spec("uipc") is not None:
            return True, None
        return False, "Install IPC backend: pip install pyuipc (Linux/Windows x86, NVIDIA GPU)."
    return True, None


def describe_entry(entry: ShowcaseScriptEntry) -> dict:
    script_path, repo_root = resolve_script_path(entry)
    extra_ok, extra_msg = optional_extra_available(entry.optional_extra)
    available = script_path is not None and extra_ok
    missing: list[str] = []
    if repo_root is None:
        env_hint = "GENESIS_WORLD_ROOT" if entry.repo == "genesis-world" else "GENESIS_NYX_ROOT"
        missing.append(f"Clone {entry.repo} and set {env_hint}, or pip install editable with examples/")
    elif script_path is None:
        missing.append(f"Script not found: {entry.script_relpath}")
    if not extra_ok and extra_msg:
        missing.append(extra_msg)
    return {
        "scenario_id": entry.scenario_id,
        "demo_name": entry.demo_name,
        "layer": entry.layer,
        "repo": entry.repo,
        "script_relpath": entry.script_relpath,
        "script_path": str(script_path) if script_path else None,
        "repo_root": str(repo_root) if repo_root else None,
        "optional_extra": entry.optional_extra,
        "optional_extra_available": extra_ok,
        "available": available,
        "missing": missing,
        "upstream_url": entry.upstream_url,
        "launch_mode": "native_subprocess",
        "demo_type": entry.demo_type,
        "telemetry_channels": list(entry.telemetry_channels) if entry.telemetry_channels else None,
        "kind": entry.kind,
        "sensor_type": entry.sensor_type,
    }


def list_catalog_entries(*, include_hidden: bool = False) -> list[ShowcaseScriptEntry]:
    if include_hidden:
        return list(SHOWCASE_ENTRIES)
    return [entry for entry in SHOWCASE_ENTRIES if entry.scenario_id not in CATALOG_EXCLUDE_IDS]
