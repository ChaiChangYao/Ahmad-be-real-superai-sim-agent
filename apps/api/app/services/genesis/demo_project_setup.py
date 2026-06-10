from __future__ import annotations

from pathlib import Path
import re

from app.models.manifest import Asset, BuildablesPhysicsManifest, Scenario
from app.services.genesis_showcase.showcase_script_catalog import get_showcase_entry

DOWNLOADS_ROOT = Path.home() / "Downloads"
DEMO_STEP_PATH = DOWNLOADS_ROOT / "robot_dog_buildables_demo.step"
DEMO_URDF_GENERATOR_PATH = DOWNLOADS_ROOT / "robot_dog_buildables_demo_urdf.py"
DEMO_URDF_PATH = DOWNLOADS_ROOT / "robot_dog_buildables_demo.urdf"
DEMO_XACRO_PATH = DOWNLOADS_ROOT / "robot_dog_buildables_demo.xacro"


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")


def _make_scenario_id(section: str, name: str) -> str:
    return f"genesis-{_slug(section)}-{_slug(name)}"


def _build_showcase_scenarios() -> list[Scenario]:
    sections: dict[str, list[str]] = {
        "physics": [
            "Rigid: franka cube",
            "Rigid: collision tower",
            "Rigid: contype",
            "FEM: hard & soft constraint",
            "MPM: tutorial",
            "MPM: sand wheel",
            "SPH: rigid",
            "SPH: + MPM",
            "PBD: liquid",
            "PBD: cloth",
            "Stable Fluid: smoke",
            "IPC: robot cloth teleop",
            "Coupler: cloth on rigid",
            "Coupler: rigid + MPM",
            "Coupler: cut dragon",
            "Coupler: water wheel",
            "Coupler: flush cubes",
            "SAP: Franka grasp rigid cube",
        ],
        "rendering": [
            "Follow entity",
            "Animated camera",
            "Nyx: hello",
            "Nyx: attached camera",
            "Nyx: PBR materials",
            "Nyx: light types",
            "Nyx: 3D Gaussian splat",
            "Nyx: object picking",
            "Nyx: multi-cam multi-env",
        ],
        "simulation-interface": [
            "Controlling a robot",
            "GUI: ImGui joint control",
            "Heterogeneous envs",
            "Domain randomization",
            "Sensor: depth camera",
            "Sensor: IMU",
            "Sensor: lidar",
            "Sensor: tactile sandbox",
            "Sensor: contact force",
            "Sensor: surface distance",
            "Sensor: temperature grid",
            "GUI: debug drawing",
            "GUI: mesh point picker",
            "GUI: mouse interaction",
            "Diff-IK controller",
            "Batched IK",
            "Drone",
            "Advanced: worm",
        ],
    }

    output: list[Scenario] = []
    for section, names in sections.items():
        for name in names:
            scenario_id = _make_scenario_id(section, name)
            command_hint = "stand"
            lowered = name.lower()
            if any(token in lowered for token in ["walk", "drone", "worm", "control", "robot", "franka", "grasp", "coupler", "mpm", "sph"]):
                command_hint = "walk_forward"
            if any(token in lowered for token in ["camera", "nyx", "render", "sensor", "gui"]):
                command_hint = "turn_left"
            if "jump" in lowered:
                command_hint = "jump"

            entry = get_showcase_entry(scenario_id)
            config: dict = {
                "genesis_layer": section,
                "genesis_demo_name": name,
                "command_hint": command_hint,
                "source": entry.upstream_url if entry else "https://github.com/Genesis-Embodied-AI/genesis-world",
                "showcase_launchable": entry is not None,
            }
            if entry:
                config["genesis_script_repo"] = entry.repo
                config["genesis_script_relpath"] = entry.script_relpath
                config["optional_extra"] = entry.optional_extra

            output.append(
                Scenario(
                    id=scenario_id,
                    name=f"[Genesis {section.title()}] {name}",
                    description=f"Genesis showcase demo reference: {name}",
                    duration_s=6.0,
                    config=config,
                )
            )
    return output


GENESIS_SHOWCASE_SCENARIOS = _build_showcase_scenarios()


BUNDLED_URDF_NAME = "robot_dog_buildables_demo.urdf"
BUNDLED_STEP_NAME = "robot_dog_buildables_demo.step"
BUNDLED_URDF_REL = Path("assets") / "imported" / BUNDLED_URDF_NAME
BUNDLED_STEP_REL = Path("assets") / "imported" / BUNDLED_STEP_NAME


def bundled_urdf_path(project_dir: Path) -> Path:
    return project_dir / BUNDLED_URDF_REL


def bundled_step_path(project_dir: Path) -> Path:
    return project_dir / BUNDLED_STEP_REL


def resolve_default_robot_urdf(project_dir: Path) -> Path | None:
    """Prefer bundled project URDF, then copy from Downloads, then Downloads path."""
    bundled = bundled_urdf_path(project_dir)
    if bundled.exists():
        return bundled.resolve()
    if DEMO_URDF_PATH.exists():
        copied = copy_downloads_robot_assets_into(project_dir)
        if copied is not None:
            return copied.resolve()
        return DEMO_URDF_PATH.resolve()
    if DEMO_XACRO_PATH.exists():
        return DEMO_XACRO_PATH.resolve()
    return None


def normalize_default_robot_dog_paths(manifest: BuildablesPhysicsManifest, project_dir: Path) -> bool:
    """Rewire manifest paths away from Downloads to bundled project assets when available."""
    changed = False
    urdf = resolve_default_robot_urdf(project_dir)
    if urdf is not None and manifest.robot_description.urdf_path != str(urdf):
        manifest.robot_description.urdf_path = str(urdf)
        manifest.robot_description.generated_from_manifest = False
        changed = True

    step = bundled_step_path(project_dir)
    assets_by_id = {asset.id: asset for asset in manifest.assets}
    for asset in manifest.assets:
        if asset.type == "step" and step.exists() and Path(asset.file_path).name == BUNDLED_STEP_NAME:
            resolved = str(step.resolve())
            if asset.file_path != resolved:
                asset.file_path = resolved
                changed = True

    if step.exists() and "asset-demo-step" not in assets_by_id:
        manifest.assets.append(
            Asset(
                id="asset-demo-step",
                name=BUNDLED_STEP_NAME,
                type="step",
                file_path=str(step.resolve()),
                original_filename=BUNDLED_STEP_NAME,
                unit_scale_to_meters=0.001,
                visual_only=True,
                generated=False,
                source_asset_id=None,
                notes="Bundled STEP source for default robot dog demo.",
            )
        )
        changed = True

    return changed


def ensure_default_robot_dog_ready(manifest: BuildablesPhysicsManifest, project_dir: Path) -> bool:
    changed = wire_external_robot_dog_assets(manifest, project_dir)
    changed = normalize_default_robot_dog_paths(manifest, project_dir) or changed
    changed = sync_genesis_showcase_scenarios(manifest) or changed
    return changed


def sync_genesis_showcase_scenarios(manifest: BuildablesPhysicsManifest) -> bool:
    existing_ids = {scenario.id for scenario in manifest.scenarios}
    added = [scenario for scenario in GENESIS_SHOWCASE_SCENARIOS if scenario.id not in existing_ids]
    if not added:
        return False
    manifest.scenarios.extend(added)
    return True


def copy_downloads_robot_assets_into(project_dir: Path) -> Path | None:
    """Copy URDF (+ STEP, meshes/) from Downloads into project assets/imported."""
    if not DEMO_URDF_PATH.exists():
        return None
    target_dir = project_dir / "assets" / "imported"
    target_dir.mkdir(parents=True, exist_ok=True)

    def _copy(name: str, src: Path) -> Path:
        dest = target_dir / name
        dest.write_bytes(src.read_bytes())
        return dest

    urdf_dest = _copy(DEMO_URDF_PATH.name, DEMO_URDF_PATH)
    if DEMO_STEP_PATH.exists():
        _copy(DEMO_STEP_PATH.name, DEMO_STEP_PATH)
    meshes_src = DOWNLOADS_ROOT / "meshes"
    if meshes_src.is_dir():
        mesh_target = target_dir / "meshes"
        mesh_target.mkdir(parents=True, exist_ok=True)
        for mesh_file in meshes_src.rglob("*"):
            if mesh_file.is_file():
                rel = mesh_file.relative_to(meshes_src)
                out = mesh_target / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(mesh_file.read_bytes())
    return urdf_dest


def wire_external_robot_dog_assets(manifest: BuildablesPhysicsManifest, project_dir: Path | None = None) -> bool:
    changed = False
    if manifest.project_mode != "default_demo":
        manifest.project_mode = "default_demo"
        changed = True
    if manifest.project_type != "robot_dog":
        manifest.project_type = "robot_dog"
        changed = True
    if "mode" not in manifest.controls:
        manifest.controls["mode"] = "remote_control"
        changed = True
    if not manifest.payloads:
        manifest.payloads.append(
            {
                "id": "payload-top-rail",
                "name": "Top Rail Payload",
                "mass_kg": 5.0,
                "attach_link_id": "body",
                "offset": {"position": {"x": 0.0, "y": 0.0, "z": 0.45}, "rotation_rpy": {"x": 0.0, "y": 0.0, "z": 0.0}},
            }
        )
        changed = True
    if not manifest.render_cameras:
        manifest.render_cameras.append(
            {
                "id": "cam-front",
                "name": "Front Camera",
                "attach_link_id": "body",
                "transform": {"position": {"x": 0.44, "y": 0.0, "z": 0.31}, "rotation_rpy": {"x": 0.0, "y": 0.0, "z": 0.0}},
                "fov_deg": 86.0,
                "output_type": "rgb",
            }
        )
        changed = True
    if not manifest.metadata_status:
        manifest.metadata_status = {"missing_control_script": False}
        changed = True

    assets_by_id = {asset.id: asset for asset in manifest.assets}

    if DEMO_STEP_PATH.exists() and "asset-demo-step" not in assets_by_id:
        manifest.assets.append(
            Asset(
                id="asset-demo-step",
                name="robot_dog_buildables_demo.step",
                type="step",
                file_path=str(DEMO_STEP_PATH),
                original_filename=DEMO_STEP_PATH.name,
                unit_scale_to_meters=0.001,
                visual_only=True,
                generated=False,
                source_asset_id=None,
                notes="External STEP source provided by user for robot dog demo.",
            )
        )
        changed = True

    if DEMO_URDF_GENERATOR_PATH.exists() and "asset-demo-urdf-generator" not in assets_by_id:
        manifest.assets.append(
            Asset(
                id="asset-demo-urdf-generator",
                name="robot_dog_buildables_demo_urdf.py",
                type="other",
                file_path=str(DEMO_URDF_GENERATOR_PATH),
                original_filename=DEMO_URDF_GENERATOR_PATH.name,
                unit_scale_to_meters=1.0,
                visual_only=False,
                generated=False,
                source_asset_id="asset-demo-step" if any(a.id == "asset-demo-step" for a in manifest.assets) else None,
                notes="URDF/Xacro generator script for Buildables robot dog.",
            )
        )
        changed = True

    urdf_path = resolve_default_robot_urdf(project_dir) if project_dir is not None else None
    if urdf_path is None:
        urdf_path = DEMO_URDF_PATH if DEMO_URDF_PATH.exists() else (DEMO_XACRO_PATH if DEMO_XACRO_PATH.exists() else None)
    if urdf_path is not None and manifest.robot_description.urdf_path != str(urdf_path):
        manifest.robot_description.urdf_path = str(urdf_path)
        manifest.robot_description.generated_from_manifest = False
        changed = True

    return changed
