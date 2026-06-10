from __future__ import annotations



from datetime import datetime, UTC

from pathlib import Path

import json

import os

import subprocess

import sys

import threading

import time

from typing import Any

from uuid import uuid4



from app.services.genesis_showcase.replay_enrich import enrich_replay_bundle
from app.services.genesis_showcase.showcase_script_catalog import (

    describe_entry,

    get_showcase_entry,

    list_catalog_entries,

    optional_extra_available,

    resolve_script_path,

)

from app.paths import repo_root, showcase_launcher_script

from app.services.genesis_workbench.session_log import append_block, append_log

from app.services.project_store import project_dir





_ACTIVE: dict[str, subprocess.Popen] = {}

_LOG_TAILERS: dict[str, threading.Thread] = {}

_LOG_OFFSETS: dict[str, dict[str, int]] = {}





def _launcher_path() -> Path:

    path = showcase_launcher_script().resolve()

    if not path.is_file():

        raise FileNotFoundError(

            f"Showcase launcher missing: {path}. Expected at apps/api/app/scripts/showcase_launcher.py"

        )

    return path





_OPENGL_HINT = (

    "Genesis viewer needs OpenGL 3+ from your graphics driver. On AMD: update AMD Adrenalin drivers, then "

    "Windows Settings → System → Display → Graphics → add python.exe → High performance (AMD Radeon). "

    "Test manually: cd genesis-world && python examples/tutorials/mpm.py"

)





def list_showcase_entries() -> list[dict]:

    return [describe_entry(entry) for entry in list_catalog_entries()]





def _run_dir(project_id: str, launch_id: str) -> Path:

    return project_dir(project_id) / "runs" / launch_id





def _read_script_text(script_path: Path) -> str:
    try:
        return script_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _script_accepts_no_vis(script_path: Path) -> bool:
    import re

    text = _read_script_text(script_path)
    if not text:
        return False
    return bool(
        re.search(r'add_argument\s*\([^)]*["\']--no-vis["\']', text)
        or re.search(r'dest\s*=\s*["\']vis["\'][^)]*["\']-nv["\']', text)
        or re.search(r'["\']-nv["\'][^)]*dest\s*=\s*["\']vis["\']', text)
    )


def _script_accepts_vis(script_path: Path) -> bool:
    import re

    text = _read_script_text(script_path)
    if not text:
        return False
    return bool(
        re.search(r'add_argument\s*\(\s*["\']-v["\']\s*,\s*["\']--vis["\']', text)
        or re.search(r'add_argument\s*\(\s*["\']--vis["\']', text)
    )


def _launch_argv(script_path: Path, *, view_mode: str) -> list[str]:

    """Launch via wrapper so we can force headless without editing upstream scripts."""

    launcher = _launcher_path()

    cmd = [sys.executable, str(launcher), "--script", str(script_path.resolve())]

    forwarded: list[str] = []
    if view_mode == "web":

        cmd.extend(["--headless", "--record-web"])

        if _script_accepts_no_vis(script_path):

            forwarded = ["--no-vis"]
            cmd.extend(["--", *forwarded])

    elif view_mode == "native" and _script_accepts_vis(script_path):

        forwarded = ["--vis"]
        cmd.extend(["--", *forwarded])

    print(f"[showcase_launcher] Forwarded args: {forwarded or '(none)'}", flush=True)
    return cmd





def _process_alive(pid: int) -> bool:

    if pid <= 0:

        return False

    if sys.platform == "win32":

        import ctypes



        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)

        if handle:

            ctypes.windll.kernel32.CloseHandle(handle)

            return True

        return False

    try:

        os.kill(pid, 0)

    except OSError:

        return False

    return True





def _purge_stale_active() -> None:

    dead = [launch_id for launch_id, proc in _ACTIVE.items() if proc.poll() is not None]

    for launch_id in dead:

        _ACTIVE.pop(launch_id, None)





def _load_launch_meta(out_dir: Path) -> dict[str, Any]:
    launch_path = out_dir / "launch.json"
    if not launch_path.is_file():
        return {}
    try:
        raw = json.loads(launch_path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _merge_launch_meta(meta: dict[str, Any], launch_meta: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(meta)
    if not launch_meta:
        return merged
    for key in ("scenario_id", "script_path", "demo_name", "demo_type", "repo", "telemetry_channels"):
        value = launch_meta.get(key)
        if value:
            merged[key] = value
    return merged


def _read_replay_file(path: Path, launch_meta: dict[str, Any] | None = None) -> dict:

    if not path.exists():

        return {"frames": [], "meta": {}, "scene": {}, "objects": []}

    try:

        raw = json.loads(path.read_text(encoding="utf-8"))

    except Exception:

        return {"frames": [], "meta": {}, "scene": {}, "objects": []}

    if isinstance(raw, list):

        return {"frames": raw, "meta": {}, "scene": {}, "objects": []}

    if isinstance(raw, dict):

        frames = raw.get("frames") if isinstance(raw.get("frames"), list) else []

        meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}

        scene = raw.get("scene") if isinstance(raw.get("scene"), dict) else {}

        objects = raw.get("objects") if isinstance(raw.get("objects"), list) else []
        raw_frames = raw.get("raw_frames") if isinstance(raw.get("raw_frames"), list) else frames
        preview_frames = raw.get("preview_frames") if isinstance(raw.get("preview_frames"), list) else []
        telemetry = raw.get("telemetry") if isinstance(raw.get("telemetry"), dict) else None
        meta = _merge_launch_meta(meta, launch_meta)

        return enrich_replay_bundle(
            {
                "frames": frames,
                "raw_frames": raw_frames,
                "preview_frames": preview_frames,
                "telemetry": telemetry,
                "meta": meta,
                "scene": scene,
                "objects": objects,
            }
        )

    return {"frames": [], "meta": {}, "scene": {}, "objects": []}





def _read_timeseries(path: Path) -> tuple[list[dict], dict]:

    data = _read_replay_file(path)

    return data["frames"], data["meta"]





def _replay_info(out_dir: Path) -> dict:

    from app.services.genesis_showcase.replay_atomic_io import effective_timeseries_path, read_manifest

    manifest = read_manifest(out_dir) or {}

    ts_path = effective_timeseries_path(out_dir, manifest)

    frame_count = int(manifest.get("frameCount") or 0)

    replay_status = str(manifest.get("status") or ("complete" if ts_path.is_file() else "unknown"))

    replay_partial = replay_status == "recording"

    replay_ready = bool(manifest.get("ready")) if manifest else ts_path.is_file()

    replay_version = int(manifest.get("version") or 0)

    replay_fps = float(manifest.get("fps") or 24.0)

    meta: dict = {}

    objects_count = 0

    robot_links = 0

    tracked = 0

    if ts_path.is_file() and (replay_ready or replay_partial or not manifest):

        launch_meta = _load_launch_meta(out_dir)
        data = _read_replay_file(ts_path, launch_meta=launch_meta)

        frames = data["frames"]

        meta = data["meta"] if isinstance(data.get("meta"), dict) else {}

        if not frame_count:

            frame_count = len(frames)

        objects_count = len(data.get("objects") or [])

        diagnostics = meta.get("diagnostics") if isinstance(meta.get("diagnostics"), dict) else {}

        robot_links = int(diagnostics.get("robot_links") or 0)

        tracked = int(diagnostics.get("tracked_objects") or objects_count)

    return {

        "replay_available": frame_count > 0 and (replay_ready or replay_partial),

        "replay_frames": frame_count,

        "replay_version": replay_version,

        "replay_ready": replay_ready,

        "replay_status": replay_status,

        "replay_partial": replay_partial,

        "replay_fps": replay_fps,

        "replay_meta": meta,

        "replay_objects": objects_count,

        "replay_robot_links": robot_links,

        "replay_tracked_objects": tracked,

        "source_frame_count": int(manifest.get("sourceFrameCount") or meta.get("source_frame_count") or frame_count),

        "preview_frame_count": int(manifest.get("previewFrameCount") or meta.get("preview_frame_count") or 0),

        "unique_pose_count": int(manifest.get("uniquePoseCount") or meta.get("unique_pose_count") or 0),

        "replay_mode": str(manifest.get("replayMode") or meta.get("replay_mode") or "raw"),

    }





def _derive_lifecycle(meta: dict, out_dir: Path) -> str:

    base = str(meta.get("status") or "idle")

    if base == "running":

        replay = _replay_info(out_dir)

        if replay["replay_frames"] and replay.get("replay_ready"):

            return "receiving_frames"

        return "running"

    if base in ("completed", "failed"):

        return base

    if base == "launching":

        return "launching"

    return base





def _tail_launch_logs(launch_id: str, out_dir: Path, stop_event: threading.Event) -> None:

    offsets = _LOG_OFFSETS.setdefault(launch_id, {"stdout.txt": 0, "stderr.txt": 0})

    while not stop_event.wait(0.75):

        proc = _ACTIVE.get(launch_id)

        if proc is not None and proc.poll() is not None:

            # One final read after process exit.

            pass

        for name in ("stdout.txt", "stderr.txt"):

            path = out_dir / name

            if not path.exists():

                continue

            try:

                text = path.read_text(encoding="utf-8", errors="ignore")

            except OSError:

                continue

            offset = offsets.get(name, 0)

            if len(text) <= offset:

                continue

            chunk = text[offset:]

            offsets[name] = len(text)

            source = "stdout" if name.startswith("stdout") else "stderr"

            append_block(f"{launch_id}/{source}", chunk)

        if proc is None or proc.poll() is not None:

            break





def _start_log_tailer(launch_id: str, out_dir: Path) -> None:

    stop_event = threading.Event()

    thread = threading.Thread(

        target=_tail_launch_logs,

        args=(launch_id, out_dir, stop_event),

        name=f"log-tail-{launch_id}",

        daemon=True,

    )

    _LOG_TAILERS[launch_id] = thread

    thread.start()





def _attach_runtime(meta: dict, out_dir: Path) -> dict:

    meta.update(_replay_info(out_dir))

    meta["lifecycle"] = _derive_lifecycle(meta, out_dir)



    if meta.get("status") == "failed":

        summary = _failure_summary(out_dir)

        if summary:

            meta["error_summary"] = summary

            if "OpenGL" in summary:

                meta["opengl_hint"] = _OPENGL_HINT

        failure = parse_launch_failure(out_dir)

        if failure:

            meta.update(failure)



    return meta





def _finalize_meta(meta: dict, out_dir: Path) -> dict:

    preserved_demo_type = meta.get("demo_type")
    preserved_telemetry_channels = meta.get("telemetry_channels")
    preserved_kind = meta.get("kind")
    preserved_sensor_type = meta.get("sensor_type")
    meta = _attach_runtime(meta, out_dir)
    if preserved_demo_type:
        meta["demo_type"] = preserved_demo_type
    if preserved_telemetry_channels:
        meta["telemetry_channels"] = preserved_telemetry_channels
    if preserved_kind:
        meta["kind"] = preserved_kind
    if preserved_sensor_type:
        meta["sensor_type"] = preserved_sensor_type
    failure = parse_launch_failure(out_dir)
    if failure:
        meta["failure_code"] = failure.get("failure_code")
        meta["failure_detail"] = failure.get("failure_detail")
        meta["suggested_fix"] = failure.get("suggested_fix")
        meta["failure_summary"] = failure.get("failure_summary")
    (out_dir / "launch.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return meta





def _failure_summary(out_dir: Path) -> str | None:

    import re



    ansi = re.compile(r"\x1b\[[0-9;]*m")



    def clean(line: str) -> str:

        return ansi.sub("", line).strip()



    chunks: list[str] = []

    for name in ("stderr.txt", "stdout.txt"):

        path = out_dir / name

        if path.exists():

            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))

    text = "\n".join(chunks)

    if not text.strip():

        return None

    cleaned_lines = [clean(line) for line in text.splitlines()]
    cleaned_lines = [line for line in cleaned_lines if line]

    for line in reversed(cleaned_lines):
        if "[WARNING]" in line or "[INFO]" in line:
            continue
        if "OpenGL 3+ context" in line or "OpenGL.error.GLError" in line or "GLError" in line:
            return f"{line} {_OPENGL_HINT}"

    traceback_start = None
    for idx in range(len(cleaned_lines) - 1, -1, -1):
        if cleaned_lines[idx].startswith("Traceback (most recent call last):"):
            traceback_start = idx
            break
    if traceback_start is not None:
        block = "\n".join(cleaned_lines[traceback_start:])
        if block.strip():
            return block

    for line in reversed(cleaned_lines):
        if "[WARNING]" in line or "[INFO]" in line:
            continue
        if line.startswith(("RuntimeError:", "ImportError:", "ModuleNotFoundError:", "Error:")):
            return line
        if "RuntimeError:" in line or "Demo crashed" in line:
            return line

    tail = "\n".join(cleaned_lines[-40:])
    return tail if tail.strip() else None


def parse_launch_failure(out_dir: Path) -> dict[str, str] | None:
    summary = _failure_summary(out_dir)
    if not summary:
        return None

    text = summary.lower()
    failure_code = "unknown"
    suggested_fix = "Review the launch log for details and verify upstream script dependencies."

    if "unrecognized arguments: --no-vis" in text or "unknown option: --no-vis" in text:
        failure_code = "invalid_cli_flag"
        suggested_fix = "This script does not accept --no-vis. Relaunch with web-only headless recording (already fixed in latest launcher)."
    elif "no such file" in text or "filenotfounderror" in text or "missing mesh" in text:
        failure_code = "missing_asset"
        suggested_fix = "Verify mesh/URDF paths exist in the upstream repo or set GENESIS_WORLD_ROOT."
    elif "importerror" in text or "modulenotfounderror" in text or "no module named 'torch'" in text or "'torch' module not available" in text:
        failure_code = "missing_dependency"
        if "torch" in text:
            suggested_fix = (
                "Genesis requires PyTorch. From repo root run: npm run setup:api "
                "(or see docs/GENESIS_SETUP_WINDOWS.md)."
            )
        else:
            suggested_fix = "Install the missing Python package or optional extra (pyuipc, gs-nyx-plugin) for this demo."
    elif "permissionerror" in text and "partial.json" in text:
        failure_code = "replay_io"
        suggested_fix = "Replay was likely written; retry launch or run npm run dev:clean if the port is stale."
    elif "opengl" in text:
        failure_code = "opengl_failure"
        suggested_fix = "Use web launch instead of native viewer, or update GPU drivers."

    return {
        "failure_code": failure_code,
        "failure_detail": summary,
        "suggested_fix": suggested_fix,
        "failure_summary": summary,
    }





def get_launch_logs(project_id: str, launch_id: str) -> dict:

    out_dir = _run_dir(project_id, launch_id)

    stdout = (out_dir / "stdout.txt").read_text(encoding="utf-8", errors="ignore") if (out_dir / "stdout.txt").exists() else ""

    stderr = (out_dir / "stderr.txt").read_text(encoding="utf-8", errors="ignore") if (out_dir / "stderr.txt").exists() else ""

    return {"launch_id": launch_id, "stdout": stdout, "stderr": stderr}





def launch_showcase_demo(

    project_id: str,

    scenario_id: str,

    *,

    view_mode: str | None = None,

    headless: bool | None = None,

) -> dict:

    entry = get_showcase_entry(scenario_id)

    if entry is None:

        raise ValueError(f"Unknown showcase scenario: {scenario_id}")



    script_path, repo_root_path = resolve_script_path(entry)

    extra_ok, extra_msg = optional_extra_available(entry.optional_extra)

    if script_path is None or repo_root_path is None:

        env_var = "GENESIS_WORLD_ROOT" if entry.repo == "genesis-world" else "GENESIS_NYX_ROOT"

        if entry.repo == "buildables":

            env_var = "repo root"

        clone = "genesis-world" if entry.repo == "genesis-world" else "genesis-nyx"

        raise FileNotFoundError(

            f"Upstream script unavailable. Clone {clone}, set {env_var} to the repo root, "

            f"then verify {entry.script_relpath} exists."

        )

    if not extra_ok:

        raise RuntimeError(extra_msg or f"Optional extra '{entry.optional_extra}' not installed.")



    if view_mode is None:

        view_mode = "web"

    if view_mode == "native" and os.getenv("BUILDABLES_ALLOW_NATIVE") != "1":

        append_log("launch", "Native view_mode requested but BUILDABLES_ALLOW_NATIVE is not set; using web.")

        view_mode = "web"

    if view_mode not in ("web", "native"):

        raise ValueError(f"Invalid view_mode: {view_mode}")



    _purge_stale_active()

    running = [p for p in _ACTIVE.values() if p.poll() is None]

    if running:

        raise RuntimeError(

            f"A demo is already running (pid {running[0].pid}). Wait for it to finish or close its window before launching again."

        )



    launch_id = f"showcase-{uuid4().hex[:10]}"

    out_dir = _run_dir(project_id, launch_id)

    out_dir.mkdir(parents=True, exist_ok=True)



    env = os.environ.copy()

    env["PYTHONUNBUFFERED"] = "1"

    env["PYTHONUTF8"] = "1"

    env["PYTHONIOENCODING"] = "utf-8"

    env["BUILDABLES_SHOWCASE_LAUNCH_ID"] = launch_id

    env["BUILDABLES_RECORD_PATH"] = str(out_dir / "state_timeseries.json")

    env["BUILDABLES_DEMO_TYPE"] = entry.demo_type
    env["BUILDABLES_SCENARIO_ID"] = entry.scenario_id
    env["BUILDABLES_CATALOG_KIND"] = entry.kind
    if entry.sensor_type:
        env["BUILDABLES_SENSOR_TYPE"] = entry.sensor_type

    if entry.telemetry_channels:

        env["BUILDABLES_TELEMETRY_CHANNELS"] = ",".join(entry.telemetry_channels)

    if view_mode == "web":

        env["BUILDABLES_WEB_RECORD"] = "1"

        env["MPLBACKEND"] = "Agg"

        env["BUILDABLES_DISABLE_NATIVE_PLOTS"] = "1"

    api_dir = str(Path(__file__).resolve().parents[3])

    env["PYTHONPATH"] = api_dir + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")



    stdout_path = out_dir / "stdout.txt"

    stderr_path = out_dir / "stderr.txt"

    stdout_f = stdout_path.open("w", encoding="utf-8")

    stderr_f = stderr_path.open("w", encoding="utf-8")



    creationflags = 0

    if sys.platform == "win32":

        creationflags |= subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]



    argv = _launch_argv(script_path, view_mode=view_mode)

    cwd = str(repo_root_path)

    if entry.repo == "buildables":

        cwd = str(repo_root())



    append_log("launch", f"Starting {launch_id} scenario={scenario_id} view_mode={view_mode}")

    append_log("launch", f"argv={argv}")

    append_log("launch", f"script={script_path.resolve()}")

    append_log("launch", f"cwd={cwd}")



    meta = {

        "launch_id": launch_id,

        "project_id": project_id,

        "scenario_id": scenario_id,

        "demo_name": entry.demo_name,

        "layer": entry.layer,

        "repo": entry.repo,

        "script_path": str(script_path),

        "repo_root": str(repo_root_path),

        "argv": argv,

        "view_mode": view_mode,

        "headless": view_mode == "web",

        "started_at": datetime.now(UTC).isoformat(),

        "status": "launching",

        "lifecycle": "launching",

        "upstream_url": entry.upstream_url,

        "demo_type": entry.demo_type,

        "telemetry_channels": list(entry.telemetry_channels) if entry.telemetry_channels else None,

        "kind": entry.kind,

        "sensor_type": entry.sensor_type,

        "note": (

            "Running physics and recording frames for the web viewer (works on AMD and NVIDIA)."

            if view_mode == "web"

            else "Opening native Genesis OS window (needs working OpenGL; may fail on some AMD laptops)."

        ),

    }

    (out_dir / "launch.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")



    proc = subprocess.Popen(

        argv,

        cwd=cwd,

        env=env,

        stdout=stdout_f,

        stderr=stderr_f,

        creationflags=creationflags,

    )

    stdout_f.close()

    stderr_f.close()

    _ACTIVE[launch_id] = proc

    _start_log_tailer(launch_id, out_dir)



    meta["pid"] = proc.pid

    meta["status"] = "running"

    meta["lifecycle"] = "running"

    (out_dir / "launch.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return meta





def get_launch_status(project_id: str, launch_id: str) -> dict:

    path = _run_dir(project_id, launch_id) / "launch.json"

    if not path.exists():

        raise FileNotFoundError(f"Launch not found: {launch_id}")

    meta = json.loads(path.read_text(encoding="utf-8"))

    out_dir = _run_dir(project_id, launch_id)

    proc = _ACTIVE.get(launch_id)



    if proc is not None:

        code = proc.poll()

        if code is None:

            meta["status"] = "running"

            meta["pid"] = proc.pid

            partial = _failure_summary(out_dir)

            if partial and "OpenGL" in partial:

                meta["warning"] = partial

            return _finalize_meta(meta, out_dir)



        meta["status"] = "completed" if code == 0 else "failed"

        meta["exit_code"] = code

        meta["ended_at"] = datetime.now(UTC).isoformat()

        append_log("launch", f"{launch_id} finished exit_code={code} status={meta['status']}")

        _ACTIVE.pop(launch_id, None)

        # Final log tail

        time.sleep(0.2)

        _tail_launch_logs(launch_id, out_dir, threading.Event())

    else:

        pid = int(meta.get("pid") or 0)

        if meta.get("status") == "running" and pid and not _process_alive(pid):

            meta["status"] = "failed"

            meta["exit_code"] = meta.get("exit_code", -1)

            meta["ended_at"] = meta.get("ended_at") or datetime.now(UTC).isoformat()

            meta["note"] = "Process exited (viewer likely crashed — common on AMD OpenGL)."

            append_log("launch", f"{launch_id} process lost pid={pid}")



    return _finalize_meta(meta, out_dir)





def get_launch_replay(project_id: str, launch_id: str) -> dict:

    from app.services.genesis_showcase.replay_atomic_io import effective_timeseries_path, read_manifest

    out_dir = _run_dir(project_id, launch_id)

    manifest = read_manifest(out_dir)

    path = effective_timeseries_path(out_dir, manifest)

    if manifest and not manifest.get("ready") and str(manifest.get("status") or "") != "recording":

        raise FileNotFoundError(f"Replay not ready for launch: {launch_id}")

    if not path.is_file():

        raise FileNotFoundError(f"No replay data for launch: {launch_id}")

    launch_meta = _load_launch_meta(out_dir)
    data = _read_replay_file(path, launch_meta=launch_meta)

    if not data["frames"]:

        raise FileNotFoundError(f"No replay frames yet for launch: {launch_id}")

    data["launch_id"] = launch_id

    data["project_id"] = project_id

    if manifest:

        data["replay_manifest"] = manifest

    if not data.get("telemetry"):
        from app.services.genesis_showcase.telemetry_recorder import load_telemetry_for_run

        telemetry = load_telemetry_for_run(out_dir)
        if telemetry is not None:
            data["telemetry"] = telemetry

    return data





def get_launch_telemetry(project_id: str, launch_id: str) -> dict[str, Any] | None:
    out_dir = _run_dir(project_id, launch_id)
    from app.services.genesis_showcase.telemetry_recorder import load_telemetry_for_run

    data = get_launch_replay(project_id, launch_id)
    telemetry = data.get("telemetry")
    if isinstance(telemetry, dict) and telemetry.get("timestamps"):
        return telemetry
    return load_telemetry_for_run(out_dir)





def get_launch_timeseries(project_id: str, launch_id: str) -> tuple[list[dict], dict]:

    from app.services.genesis_showcase.replay_atomic_io import read_manifest

    data = get_launch_replay(project_id, launch_id)

    meta = dict(data.get("meta") or {})
    if data.get("telemetry") is not None:
        meta["telemetry"] = data.get("telemetry")

    manifest = data.get("replay_manifest") or read_manifest(_run_dir(project_id, launch_id))

    if manifest:

        meta["replay_manifest"] = manifest

        meta["replay_fps"] = manifest.get("fps")

    meta["scene"] = data.get("scene")

    meta["objects"] = data.get("objects")

    return data["frames"], meta





def get_launch_mesh_path(project_id: str, launch_id: str, mesh_path: str) -> Path:

    safe = mesh_path.replace("\\", "/").lstrip("/")

    if ".." in safe or not safe.startswith("meshes/") or not safe.endswith(".json"):

        raise ValueError(f"Invalid mesh path: {mesh_path}")

    path = (_run_dir(project_id, launch_id) / safe).resolve()

    run_root = _run_dir(project_id, launch_id).resolve()

    if run_root not in path.parents and path.parent != run_root:

        raise ValueError(f"Invalid mesh path: {mesh_path}")

    if not path.is_file():

        raise FileNotFoundError(f"Mesh not found: {mesh_path}")

    return path

