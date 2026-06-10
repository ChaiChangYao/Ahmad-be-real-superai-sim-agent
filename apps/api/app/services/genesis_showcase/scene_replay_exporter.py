"""Discover Genesis scene objects and record link-level transforms for web replay."""
from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from app.services.genesis_showcase.franka_visual_defs import attach_franka_fallback_assets
from app.services.genesis_showcase.franka_asset_meshes import export_franka_link_meshes
from app.services.genesis_showcase.replay_atomic_io import write_replay_bundle
from app.services.genesis_showcase.replay_motion_diagnostics import (
    analyze_replay_motion,
    choose_preview_mode,
    log_motion_diagnostics,
    should_generate_smooth_preview,
    _aggregate_delta,
)
from app.services.genesis_showcase.replay_smooth_preview import generate_dense_trim_preview, generate_smooth_preview
from app.services.genesis_showcase.showcase_script_catalog import infer_demo_type_from_script
from app.services.genesis_showcase.sensor_capture import (
    CONTACT_FOOT_ORDER,
    DEPTH_CAMERA_NAMES,
    capture_contact_force_sample,
    capture_depth_cameras,
    capture_tactile_frame,
    extract_lidar_points,
)
from app.services.genesis_showcase.telemetry_recorder import (
    TelemetryRecorder,
    build_imu_telemetry_sample,
    install_telemetry_capture,
    load_npz_telemetry_fallback,
    write_telemetry_companion,
)


MAX_TRIS_PER_LINK = 5000
MAX_VERTS_PER_LINK = 15000


def _vec3(value) -> list[float]:
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, (list, tuple)) and value and isinstance(value[0], (list, tuple)):
        value = value[0]
    return [float(value[0]), float(value[1]), float(value[2])]


def _quat4(value) -> list[float]:
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, (list, tuple)) and value and isinstance(value[0], (list, tuple)):
        value = value[0]
    return [float(value[0]), float(value[1]), float(value[2]), float(value[3])]


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-/]", "_", value)


def _mesh_file_id(object_id: str) -> str:
    return _safe_id(object_id).replace("/", "__")


def _entity_name(ent) -> str:
    name = getattr(ent, "name", None)
    if name:
        return str(name)
    morph = getattr(ent, "morph", None)
    morph_name = type(morph).__name__.lower() if morph is not None else "entity"
    uid = str(getattr(ent, "uid", id(ent)))
    short = uid.replace("<", "").replace(">", "")[:7]
    return f"{morph_name.split('morph')[-1] or 'entity'}_{short}"


def _morph_info(ent) -> tuple[str, str, bool]:
    morph = getattr(ent, "morph", None)
    if morph is None:
        return "unknown", "", False
    morph_type = type(morph).__name__.lower()
    morph_file = str(getattr(morph, "file", "") or "")
    is_articulated = morph_type in {"mjcf", "urdf"} or morph_file.endswith((".xml", ".urdf"))
    if not is_articulated:
        links = getattr(ent, "_links", None)
        if links is not None and len(links) > 1:
            is_articulated = True
    return morph_type, morph_file, is_articulated


def _is_franka_morph(morph_file: str) -> bool:
    text = morph_file.lower()
    return "franka" in text or "franka_panda" in text or "franka_cube" in text


def _geom_type_name(geom) -> str:
    try:
        import genesis as gs

        gtype = getattr(geom, "type", None)
        if gtype == gs.GEOM_TYPE.BOX:
            return "box"
        if gtype == gs.GEOM_TYPE.SPHERE:
            return "sphere"
        if gtype == gs.GEOM_TYPE.CAPSULE:
            return "capsule"
        if gtype == gs.GEOM_TYPE.CYLINDER:
            return "cylinder"
        if gtype == gs.GEOM_TYPE.PLANE:
            return "plane"
        return "mesh"
    except Exception:
        return "mesh"


def _aabb_size(verts) -> list[float]:
    import numpy as np

    arr = np.asarray(verts)
    if arr.size == 0:
        return [0.1, 0.1, 0.1]
    mn = arr.min(axis=0)
    mx = arr.max(axis=0)
    return [float(mx[i] - mn[i]) for i in range(3)]


def _export_link_mesh(link, object_id: str, mesh_dir: Path) -> str | None:
    vgeoms = getattr(link, "vgeoms", None) or getattr(link, "_vgeoms", [])
    if not vgeoms:
        return None
    try:
        import numpy as np
        import trimesh
    except ImportError:
        return None

    meshes = []
    for vgeom in vgeoms:
        try:
            tm = vgeom.get_trimesh()
            if tm is not None and len(tm.vertices) > 0:
                meshes.append(tm)
        except Exception:
            verts = getattr(vgeom, "_init_vverts", None)
            faces = getattr(vgeom, "_init_vfaces", None)
            if verts is not None and faces is not None and len(verts) > 0:
                meshes.append(trimesh.Trimesh(vertices=np.asarray(verts), faces=np.asarray(faces), process=False))

    if not meshes:
        return None

    combined = trimesh.util.concatenate(meshes) if len(meshes) > 1 else meshes[0]
    if len(combined.faces) > MAX_TRIS_PER_LINK:
        try:
            combined = combined.simplify_quadric_decimation(MAX_TRIS_PER_LINK)
        except Exception:
            pass
    if len(combined.faces) > MAX_TRIS_PER_LINK:
        step = max(1, len(combined.faces) // MAX_TRIS_PER_LINK)
        combined = trimesh.Trimesh(
            vertices=combined.vertices,
            faces=combined.faces[::step],
            process=False,
        )
    if len(combined.vertices) > MAX_VERTS_PER_LINK:
        try:
            target_faces = max(500, min(MAX_TRIS_PER_LINK, len(combined.faces) // 4))
            combined = combined.simplify_quadric_decimation(target_faces)
        except Exception:
            pass
    if len(combined.vertices) > MAX_VERTS_PER_LINK:
        print(
            f"[showcase_launcher] Mesh too large for web export ({len(combined.vertices)} verts on {object_id}); "
            "using procedural link fallback",
            flush=True,
        )
        return None

    mesh_dir.mkdir(parents=True, exist_ok=True)
    rel_name = f"meshes/{_mesh_file_id(object_id)}.json"
    out_path = mesh_dir.parent / rel_name
    payload = {
        "positions": combined.vertices.astype(float).reshape(-1).tolist(),
        "indices": combined.faces.astype(int).reshape(-1).tolist(),
    }
    out_path.write_text(json.dumps(payload), encoding="utf-8")
    return rel_name


def _stable_object_id(
    *,
    morph_type: str,
    morph_file: str,
    script_path: str,
    link_name: str | None,
    is_articulated: bool,
    is_franka: bool,
) -> str:
    if link_name and is_franka:
        return f"franka/{link_name}"
    if not is_articulated:
        if "plane" in morph_type:
            return "env/floor"
        if "box" in morph_type:
            return "manipuland/cube"
    if link_name:
        return f"robot/{link_name}"
    return _safe_id(link_name or morph_type)


def _simple_object_visual(ent, morph_type: str, object_id: str) -> dict:
    morph = getattr(ent, "morph", None)
    mt = morph_type.lower()
    if "plane" in mt or object_id == "env/floor":
        return {"kind": "checker_floor", "size": [4.0, 4.0]}
    if "sphere" in mt:
        radius = float(getattr(morph, "radius", 0.05) or 0.05)
        return {"kind": "sphere", "radius": radius, "color": "#94a3b8"}
    if "capsule" in mt:
        radius = float(getattr(morph, "radius", 0.04) or 0.04)
        length = float(getattr(morph, "length", 0.1) or 0.1)
        return {"kind": "capsule", "radius": radius, "length": length, "color": "#94a3b8"}
    if "cylinder" in mt:
        radius = float(getattr(morph, "radius", 0.04) or 0.04)
        height = float(getattr(morph, "height", 0.1) or 0.1)
        return {"kind": "cylinder", "radius": radius, "height": height, "color": "#94a3b8"}
    if "box" in mt or object_id == "manipuland/cube":
        raw_size = getattr(morph, "size", None) if morph is not None else None
        size = _vec3(raw_size) if raw_size is not None else [0.04, 0.04, 0.04]
        return {"kind": "box", "size": size, "color": "#c54b5d"}
    return {"kind": "box", "size": [0.12, 0.12, 0.12], "color": "#94a3b8"}


class SceneReplayExporter:
    def __init__(self, record_path: Path, script_path: str = "", *, demo_type: str = "motion") -> None:
        self.record_path = record_path
        self.mesh_dir = record_path.parent / "meshes"
        self.script_path = script_path
        self.demo_type = demo_type or "motion"
        self.frames: list[dict] = []
        self.objects: list[dict] = []
        self._imu_sensors: list[Any] = []
        self._lidar_sensors: list[Any] = []
        self._depth_cameras: list[tuple[str, Any]] = []
        self._tactile_sensors: list[Any] = []
        self._contact_sensors: list[tuple[str, Any]] = []
        self._contact_sensor_count = 0
        self._depth_camera_count = 0
        self.telemetry = TelemetryRecorder()
        self.scene: dict[str, Any] = {
            "units": "meters",
            "upAxis": "z",
            "assets": [],
            "recording_fps": 100,
            "playback_fps": 24,
        }
        self.meta: dict[str, Any] = {"diagnostics": {}, "entities": {}}
        self._trackers: dict[str, Callable[[], dict]] = {}
        self._entities: list[Any] = []
        self._dt = 0.01
        self._diagnostics = {
            "top_level_entities": 0,
            "robot_links": 0,
            "visual_geoms": 0,
            "meshes_found": 0,
            "meshes_exported": 0,
            "mesh_export_failures": 0,
            "tracked_objects": 0,
            "franka_fallback": False,
        }

    def discover_scene(self, scene) -> None:
        entities = getattr(scene, "entities", []) or []
        self._diagnostics["top_level_entities"] = len(entities)
        sim = getattr(scene, "sim", None)
        self._dt = float(getattr(sim, "dt", 0.01) or 0.01)
        self.telemetry.set_dt(self._dt)

        franka_mesh_map: dict[str, str] = {}
        franka_entities = [
            e for e in entities
            if _is_franka_morph(str(getattr(getattr(e, "morph", None), "file", "") or ""))
        ]
        if franka_entities:
            franka_mesh_map = export_franka_link_meshes(self.mesh_dir)
            if franka_mesh_map:
                self._diagnostics["meshes_exported"] += len(franka_mesh_map)
                print(f"[showcase_launcher] Franka OBJ meshes exported: {len(franka_mesh_map)} links", flush=True)

        for ent in entities:
            self._entities.append(ent)
            morph_type, morph_file, is_articulated = _morph_info(ent)
            is_franka = _is_franka_morph(morph_file)

            if is_articulated:
                links = getattr(ent, "_links", []) or []
                self._diagnostics["robot_links"] += len(links)
                for link in links:
                    link_name = getattr(link, "name", None) or f"link_{getattr(link, 'idx_local', 0)}"
                    object_id = _stable_object_id(
                        morph_type=morph_type,
                        morph_file=morph_file,
                        script_path=self.script_path,
                        link_name=str(link_name),
                        is_articulated=True,
                        is_franka=is_franka,
                    )
                    vgeoms = getattr(link, "vgeoms", []) or []
                    geoms = getattr(link, "geoms", []) or []
                    self._diagnostics["visual_geoms"] += len(vgeoms) + len(geoms)

                    visual: dict[str, Any] = {"kind": "robot_link", "color": "#e8e8e8"}
                    mesh_path = franka_mesh_map.get(str(link_name)) if is_franka else None
                    if mesh_path:
                        visual["meshPath"] = mesh_path
                        visual["meshSource"] = "franka_obj_assets"
                    elif not is_franka and (vgeoms or geoms):
                        self._diagnostics["meshes_found"] += 1
                        mesh_path = _export_link_mesh(link, object_id.replace("/", "__"), self.mesh_dir)
                        if mesh_path:
                            visual["meshPath"] = mesh_path
                            self._diagnostics["meshes_exported"] += 1
                        else:
                            self._diagnostics["mesh_export_failures"] += 1

                    obj = {
                        "id": object_id,
                        "type": "robot_link",
                        "parent": "franka" if is_franka else _entity_name(ent),
                        "link_name": link_name,
                        "visual": visual,
                    }
                    if is_franka:
                        obj["robot_model"] = "franka_panda"
                    self.objects.append(obj)
                    self.meta["entities"][object_id] = visual

                    def make_tracker(entity=ent, lname=str(link_name), fallback=link, oid=object_id):
                        def capture() -> dict:
                            lnk = fallback
                            for candidate in getattr(entity, "_links", []) or []:
                                if str(getattr(candidate, "name", "")) == lname:
                                    lnk = candidate
                                    break
                            return {
                                "position": _vec3(lnk.get_pos()),
                                "quaternion": _quat4(lnk.get_quat()),
                            }

                        return capture

                    self._trackers[object_id] = make_tracker()
            else:
                object_id = _stable_object_id(
                    morph_type=morph_type,
                    morph_file=morph_file,
                    script_path=self.script_path,
                    link_name=None,
                    is_articulated=False,
                    is_franka=False,
                )
                visual = _simple_object_visual(ent, morph_type, object_id)
                obj = {"id": object_id, "type": morph_type.split("morph")[-1] or "rigid_body", "visual": visual}
                self.objects.append(obj)
                self.meta["entities"][object_id] = visual

                def make_entity_tracker(entity=ent, oid=object_id):
                    def capture() -> dict:
                        return {
                            "position": _vec3(entity.get_pos()),
                            "quaternion": _quat4(entity.get_quat()),
                        }

                    return capture

                self._trackers[object_id] = make_entity_tracker()

        if any(o.get("robot_model") == "franka_panda" for o in self.objects):
            self.scene["robot_model"] = "franka_panda"
            self._diagnostics["franka_fallback"] = attach_franka_fallback_assets(self.scene, self.objects)

        self.scene["recording_fps"] = round(1.0 / self._dt) if self._dt > 0 else 100
        self.scene["playback_fps"] = 24
        self._diagnostics["tracked_objects"] = len(self._trackers)
        transform_sample: list[dict] = []
        for obj in self.objects[:4]:
            tracker = self._trackers.get(obj["id"])
            if tracker is None:
                continue
            try:
                transform_sample.append({"id": obj["id"], **tracker()})
            except Exception:
                continue
        self.meta["diagnostics"] = dict(self._diagnostics)
        if transform_sample:
            self.meta["diagnostics"]["transform_sample"] = transform_sample
            print(
                f"[showcase_launcher] Transform sample (raw Genesis, upAxis=z): "
                f"{json.dumps(transform_sample[:4])}",
                flush=True,
            )
        self._log_diagnostics()

    def _capture_imu_telemetry(self, step: int) -> None:
        if self.demo_type not in ("telemetry", "hybrid") or not self._imu_sensors:
            return
        imu = self._imu_sensors[0]
        try:
            sample = build_imu_telemetry_sample(imu)
            self.telemetry.append_sample(sample, t=round(step * self._dt, 6), step=step)
        except Exception as exc:
            if step == 0:
                print(f"[showcase_launcher] IMU telemetry capture failed: {exc}", flush=True)

    def _capture_contact_force_telemetry(self, step: int) -> None:
        if self.demo_type not in ("telemetry", "hybrid") or not self._contact_sensors:
            return
        try:
            sample = capture_contact_force_sample(self._contact_sensors)
            if sample:
                self.telemetry.append_sample(sample, t=round(step * self._dt, 6), step=step)
        except Exception as exc:
            if step == 0:
                print(f"[showcase_launcher] Contact force telemetry capture failed: {exc}", flush=True)

    def _capture_depth_telemetry(self, step: int) -> None:
        if self.demo_type not in ("telemetry", "hybrid") or not self._depth_cameras:
            return
        try:
            frames = capture_depth_cameras(self._depth_cameras)
            if frames:
                self.telemetry.append_depth_frame(frames, t=round(step * self._dt, 6), step=step)
        except Exception as exc:
            if step == 0:
                print(f"[showcase_launcher] Depth camera telemetry capture failed: {exc}", flush=True)

    def _capture_tactile_telemetry(self, step: int) -> None:
        if self.demo_type not in ("telemetry", "hybrid") or not self._tactile_sensors:
            return
        sensor = self._tactile_sensors[0]
        try:
            frame = capture_tactile_frame(sensor)
            if frame:
                self.telemetry.append_tactile_frame(frame, t=round(step * self._dt, 6), step=step)
        except Exception as exc:
            if step == 0:
                print(f"[showcase_launcher] Tactile telemetry capture failed: {exc}", flush=True)

    def _capture_lidar_points(self, step: int) -> list[list[float]]:
        if self.demo_type not in ("telemetry", "hybrid") or not self._lidar_sensors:
            return []
        points: list[list[float]] = []
        for sensor in self._lidar_sensors:
            try:
                hits = extract_lidar_points(sensor)
                if hits:
                    points.extend(hits)
            except Exception as exc:
                if step == 0:
                    print(f"[showcase_launcher] LiDAR point capture failed: {exc}", flush=True)
        return points

    def record_frame(self, step: int) -> None:
        transforms: dict[str, dict] = {}
        qpos: dict[str, list[float]] = {}
        for object_id, capture in self._trackers.items():
            try:
                transforms[object_id] = copy.deepcopy(capture())
            except Exception:
                continue
        for ent in self._entities:
            name = _entity_name(ent)
            if hasattr(ent, "get_dofs_position"):
                try:
                    raw = ent.get_dofs_position()
                    if hasattr(raw, "tolist"):
                        qpos[name] = [float(v) for v in raw.tolist()]
                    elif isinstance(raw, (list, tuple)):
                        qpos[name] = [float(v) for v in raw]
                except Exception:
                    continue
        lidar_points = self._capture_lidar_points(step)
        frame_payload: dict[str, Any] = {
            "t": round(step * self._dt, 6),
            "step": step,
            "transforms": copy.deepcopy(transforms),
            "qpos": copy.deepcopy(qpos),
        }
        if lidar_points:
            frame_payload["lidar_points"] = lidar_points
        self.frames.append(frame_payload)
        if step % 10 == 0 and self.frames:
            robot_ids = [o["id"] for o in self.objects if o.get("type") == "robot_link"]
            sample_id = robot_ids[0] if robot_ids else None
            max_delta = 0.0
            if len(self.frames) > 1 and robot_ids:
                prev_frame = self.frames[-2]
                cur_frame = self.frames[-1]
                delta_info = _aggregate_delta(prev_frame, cur_frame, robot_ids)
                per_object = delta_info.get("per_object") or {}
                if per_object:
                    sample_id = max(per_object.items(), key=lambda item: item[1])[0]
                    max_delta = float(per_object.get(sample_id, 0.0))
                else:
                    max_delta = float(delta_info.get("max_pos", 0.0))
            elif sample_id and len(self.frames) > 1:
                prev = self.frames[-2]["transforms"].get(sample_id, {})
                cur = self.frames[-1]["transforms"].get(sample_id, {})
                pp = prev.get("position") or [0, 0, 0]
                cp = cur.get("position") or [0, 0, 0]
                max_delta = sum((cp[i] - pp[i]) ** 2 for i in range(3)) ** 0.5
            if sample_id:
                print(
                    f"[showcase_launcher] Frame {step}: link {sample_id} pos delta={max_delta:.6f} qpos_keys={len(qpos)}",
                    flush=True,
                )
        self._capture_imu_telemetry(step)
        self._capture_contact_force_telemetry(step)
        self._capture_depth_telemetry(step)
        self._capture_tactile_telemetry(step)

    def _tracked_object_ids(self) -> list[str]:
        return [
            o["id"]
            for o in self.objects
            if o.get("type") != "checker_floor" and not str(o["id"]).startswith("env/")
        ]

    def flush(self, *, partial: bool = False) -> None:
        if not self.frames:
            return
        object_ids = self._tracked_object_ids()
        raw_frames = copy.deepcopy(self.frames)
        motion_diag = analyze_replay_motion(raw_frames, object_ids)
        log_motion_diagnostics(motion_diag)

        preview_frames: list[dict] = raw_frames
        preview_meta: dict = {"mode": "raw"}
        visual_trim_applied = False
        apply_visual_trim = self.demo_type == "motion" and not partial

        if apply_visual_trim and should_generate_smooth_preview(motion_diag, len(raw_frames)):
            preview_mode = choose_preview_mode(motion_diag, len(raw_frames))
            if preview_mode == "dense_trim":
                preview_frames, preview_meta = generate_dense_trim_preview(
                    raw_frames,
                    object_ids=object_ids,
                    preview_fps=float(self.scene.get("playback_fps") or 24),
                )
            else:
                preview_frames, preview_meta = generate_smooth_preview(
                    raw_frames,
                    object_ids=object_ids,
                    preview_fps=float(self.scene.get("playback_fps") or 24),
                )
            visual_trim_applied = len(preview_frames) != len(raw_frames)
            validation = preview_meta.get("validation") or {}
            trim_info = preview_meta.get("trim_info") or {}
            print(
                f"[showcase_launcher] Preview ({preview_meta.get('mode')}): {len(raw_frames)} raw frames -> "
                f"{len(preview_frames)} preview frames "
                f"(head={trim_info.get('frozen_head_length', 0)}, tail={trim_info.get('frozen_tail_length', 0)}, "
                f"longest_freeze={validation.get('longest_frozen_run')}, "
                f"max_jump={validation.get('max_position_jump')})",
                flush=True,
            )
        elif not partial:
            preview_frames = raw_frames

        telemetry_bundle = self.telemetry.to_bundle()
        if (
            telemetry_bundle is None
            and not partial
            and self.demo_type in ("telemetry", "hybrid")
        ):
            telemetry_bundle = load_npz_telemetry_fallback(self.record_path.parent)
        telemetry_diag = self.telemetry.diagnostics()
        if telemetry_bundle is not None:
            telemetry_diag = {
                **telemetry_diag,
                "telemetry_sample_count": len(telemetry_bundle.get("timestamps") or []),
            }

        self._diagnostics["motion_diagnostics"] = motion_diag
        self._diagnostics["source_frame_count"] = len(raw_frames)
        self._diagnostics["unique_pose_count"] = motion_diag.get("unique_pose_count")
        self._diagnostics["longest_freeze_run"] = motion_diag.get("longest_freeze_run")
        self._diagnostics["preview_frame_count"] = len(preview_frames)
        self._diagnostics["recorder_issue"] = motion_diag.get("recorder_issue")
        self.meta["diagnostics"] = dict(self._diagnostics)
        self.meta["diagnostics"]["replay_frames"] = len(preview_frames if not partial else raw_frames)
        self.meta["motion_diagnostics"] = motion_diag
        self.meta["source_frame_count"] = len(raw_frames)
        self.meta["unique_pose_count"] = motion_diag.get("unique_pose_count")
        self.meta["preview_frame_count"] = len(preview_frames)
        self.meta["preview_meta"] = preview_meta
        self.meta["preview_validation"] = preview_meta.get("validation")
        self.meta["demo_type"] = self.demo_type
        self.meta["script_path"] = self.script_path
        catalog_kind = os.environ.get("BUILDABLES_CATALOG_KIND")
        sensor_type = os.environ.get("BUILDABLES_SENSOR_TYPE")
        if catalog_kind:
            self.meta["kind"] = catalog_kind
        if sensor_type:
            self.meta["sensor_type"] = sensor_type
        scenario_id = os.environ.get("BUILDABLES_SCENARIO_ID")
        if scenario_id:
            self.meta["scenario_id"] = scenario_id
        telemetry_channels = os.environ.get("BUILDABLES_TELEMETRY_CHANNELS")
        if telemetry_channels:
            self.meta["telemetry_channels"] = [part.strip() for part in telemetry_channels.split(",") if part.strip()]
        self.meta["visual_raw_frame_count"] = len(raw_frames)
        self.meta["telemetry_sample_count"] = telemetry_diag.get("telemetry_sample_count", 0)
        self.meta["telemetry_distinct_sample_count"] = telemetry_diag.get("telemetry_distinct_sample_count", 0)
        self.meta["longest_repeated_telemetry_run"] = telemetry_diag.get("longest_repeated_telemetry_run", 0)
        self.meta["visual_trim_applied"] = visual_trim_applied
        self.meta["telemetry_trim_applied"] = telemetry_diag.get("telemetry_trim_applied", False)
        self.meta["trim_reason"] = (
            "motion_demo_visual_trim"
            if visual_trim_applied
            else ("telemetry_demo_preserve_samples" if self.demo_type in ("telemetry", "hybrid") else "none")
        )
        self.meta["replay_mode"] = (
            str(preview_meta.get("mode"))
            if apply_visual_trim and preview_meta.get("mode") not in (None, "raw")
            else ("smooth_preview" if apply_visual_trim and len(preview_frames) != len(raw_frames) else "raw")
        )
        self.meta["playback_fps"] = 24

        playback_frames = raw_frames if partial else preview_frames
        if not partial and self.demo_type in ("telemetry", "hybrid") and telemetry_bundle is not None:
            tele_len = len(telemetry_bundle.get("timestamps") or [])
            if tele_len > len(playback_frames):
                self.meta["timeline_driver"] = "telemetry"
                self.meta["timeline_length"] = tele_len
            else:
                self.meta["timeline_driver"] = "visual"
                self.meta["timeline_length"] = len(playback_frames)

        payload = {
            "scene": self.scene,
            "objects": self.objects,
            "frames": playback_frames,
            "raw_frames": raw_frames,
            "preview_frames": preview_frames if not partial else [],
            "meta": self.meta,
        }
        if telemetry_bundle is not None:
            payload["telemetry"] = telemetry_bundle
        fps = round(1.0 / self._dt) if self._dt > 0 else 24.0
        self.scene["recording_fps"] = fps
        self.scene["playback_fps"] = 24
        self.scene["sourceFrameCount"] = len(raw_frames)
        self.scene["uniquePoseCount"] = motion_diag.get("unique_pose_count")
        self.scene["previewFrameCount"] = len(preview_frames)
        self.scene["mode"] = self.meta["replay_mode"]
        try:
            manifest = write_replay_bundle(
                self.record_path.parent,
                payload,
                partial=partial,
                fps=float(self.scene.get("playback_fps") or 24),
                up_axis=str(self.scene.get("upAxis") or "z"),
                source_frame_count=len(raw_frames),
                preview_frame_count=len(preview_frames),
                unique_pose_count=int(motion_diag.get("unique_pose_count") or 0),
                replay_mode=str(self.meta["replay_mode"]),
            )
        except OSError as exc:
            if partial:
                print(
                    f"[showcase_launcher] Partial replay write skipped (file busy): {exc}",
                    flush=True,
                )
                return
            raise
        if telemetry_bundle is not None:
            write_telemetry_companion(self.record_path.parent, telemetry_bundle, partial=partial)
        tag = "partial" if partial else "final"
        print(
            f"[showcase_launcher] Wrote {len(playback_frames)} replay frames ({tag}, v{manifest.get('version')}) · "
            f"raw={len(raw_frames)} unique_poses={motion_diag.get('unique_pose_count')} preview={len(preview_frames)} · "
            f"{self._diagnostics['tracked_objects']} objects "
            f"({self._diagnostics['robot_links']} robot links) "
            f"to {self.record_path}",
            flush=True,
        )

    def _log_diagnostics(self) -> None:
        d = self._diagnostics
        print(
            f"[showcase_launcher] Scene export: top_level={d['top_level_entities']} "
            f"robot_links={d['robot_links']} visual_geoms={d['visual_geoms']} "
            f"meshes_exported={d['meshes_exported']} tracked_objects={d['tracked_objects']} "
            f"franka_fallback={d['franka_fallback']}",
            flush=True,
        )


def install_scene_recorder(record_path: Path, script_path: str, *, demo_type: str | None = None) -> dict:
    """Patch gs.Scene.build/step to record rich replay data. Returns flush handle dict."""
    import genesis as gs

    resolved_demo_type = demo_type or os.environ.get("BUILDABLES_DEMO_TYPE") or infer_demo_type_from_script(script_path)
    if resolved_demo_type not in ("motion", "telemetry", "hybrid"):
        resolved_demo_type = infer_demo_type_from_script(script_path)

    exporter = SceneReplayExporter(record_path, script_path=script_path, demo_type=str(resolved_demo_type))
    install_telemetry_capture(exporter.telemetry)

    if not getattr(gs.Scene.add_sensor, "_buildables_imu_patch", False):
        original_add_sensor = gs.Scene.add_sensor

        def patched_add_sensor(self, sensor_options, *args, **kwargs):
            sensor = original_add_sensor(self, sensor_options, *args, **kwargs)
            if exporter.demo_type in ("telemetry", "hybrid"):
                cfg_name = type(sensor_options).__name__
                if "IMU" in cfg_name or callable(getattr(sensor, "read_ground_truth", None)):
                    exporter._imu_sensors.append(sensor)
                    exporter.telemetry.imu_capture_active = True
                    print("[showcase_launcher] IMU sensor registered for per-step telemetry capture", flush=True)
                elif "Lidar" in cfg_name:
                    exporter._lidar_sensors.append(sensor)
                    print("[showcase_launcher] LiDAR sensor registered for point capture", flush=True)
                elif "DepthCamera" in cfg_name:
                    idx = exporter._depth_camera_count
                    name = DEPTH_CAMERA_NAMES[idx] if idx < len(DEPTH_CAMERA_NAMES) else f"cam_{idx}"
                    exporter._depth_camera_count += 1
                    exporter._depth_cameras.append((name, sensor))
                    print(f"[showcase_launcher] Depth camera registered ({name})", flush=True)
                elif "ElastomerTaxel" in cfg_name or "Taxel" in cfg_name:
                    exporter._tactile_sensors.append(sensor)
                    print("[showcase_launcher] Tactile sensor registered for telemetry capture", flush=True)
                elif "ContactForce" in cfg_name:
                    idx = exporter._contact_sensor_count
                    link_name = CONTACT_FOOT_ORDER[idx] if idx < len(CONTACT_FOOT_ORDER) else f"foot_{idx}"
                    exporter._contact_sensor_count += 1
                    exporter._contact_sensors.append((link_name, sensor))
                    print(f"[showcase_launcher] Contact force sensor registered ({link_name})", flush=True)
                elif callable(getattr(sensor, "read", None)):
                    print(f"[showcase_launcher] Generic sensor registered ({cfg_name})", flush=True)
            return sensor

        patched_add_sensor._buildables_imu_patch = True  # type: ignore[attr-defined]
        gs.Scene.add_sensor = patched_add_sensor  # type: ignore[method-assign]

    original_build = gs.Scene.build

    def patched_build(self, *args, **kwargs):
        out = original_build(self, *args, **kwargs)
        exporter.discover_scene(self)
        original_step = self.step
        step_idx = [0]

        def recording_step(*a, **kw):
            result = original_step(*a, **kw)
            exporter.record_frame(step_idx[0])
            step_idx[0] += 1
            if step_idx[0] % 30 == 0:
                exporter.flush(partial=True)
            return result

        self.step = recording_step  # type: ignore[method-assign]
        return out

    gs.Scene.build = patched_build  # type: ignore[method-assign]
    return {"flush": exporter.flush, "exporter": exporter}
