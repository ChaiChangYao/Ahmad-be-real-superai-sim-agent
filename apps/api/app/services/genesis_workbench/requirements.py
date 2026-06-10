from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from app.paths import repo_root
from app.services.gpu_detect import nvidia_gpu_hint
from app.services.genesis_showcase.example_script_runner import list_showcase_entries
from app.services.genesis_showcase.showcase_script_catalog import (
    describe_entry,
    get_showcase_entry,
    optional_extra_available,
    resolve_repo_root,
)
from app.services.project_store import project_dir


def _python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def _package_version(name: str) -> str | None:
    try:
        import importlib.metadata as md

        return md.version(name)
    except Exception:
        return None


def _torch_version() -> str | None:
    try:
        import torch

        return torch.__version__
    except Exception:
        return None


def _checklist_item(
    *,
    id: str,
    label: str,
    status: str,
    detail: str = "",
    commands: list[str] | None = None,
    links: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "id": id,
        "label": label,
        "status": status,
        "detail": detail,
        "commands": commands or [],
        "links": links or [],
    }


def build_readiness() -> dict[str, Any]:
    world_root = resolve_repo_root("genesis-world")
    nyx_root = resolve_repo_root("genesis-nyx")
    entries = list_showcase_entries()
    available = sum(1 for e in entries if e["available"])
    pyuipc_ok, pyuipc_msg = optional_extra_available("pyuipc")
    nyx_ok, nyx_msg = optional_extra_available("nyx")

    return {
        "platform": platform.system(),
        "python_version": _python_version(),
        "torch_version": _torch_version(),
        "genesis_world_pip": _package_version("genesis-world"),
        "genesis_world_root": str(world_root) if world_root else None,
        "genesis_nyx_root": str(nyx_root) if nyx_root else None,
        "genesis_world_root_env": os.getenv("GENESIS_WORLD_ROOT"),
        "genesis_nyx_root_env": os.getenv("GENESIS_NYX_ROOT"),
        "repo_root": str(repo_root()),
        "showcase": {"total": len(entries), "available": available},
        "optional_extras": {
            "pyuipc": {"installed": pyuipc_ok, "message": pyuipc_msg},
            "gs_nyx_plugin": {"installed": nyx_ok, "message": nyx_msg},
            "quadrants": {"installed": True, "message": "Bundled with genesis-world; no separate install"},
        },
        "gpu": nvidia_gpu_hint(),
    }


def _environment_requirements() -> dict[str, Any]:
    world_root = resolve_repo_root("genesis-world")
    nyx_root = resolve_repo_root("genesis-nyx")
    items: list[dict[str, Any]] = []

    items.append(
        _checklist_item(
            id="python",
            label="Python 3.10–3.13 + PyTorch",
            status="ok" if _torch_version() else "warning",
            detail=f"Python {_python_version()}" + (f", PyTorch {_torch_version()}" if _torch_version() else " — install PyTorch per genesis-world docs"),
            links=[{"label": "Genesis docs", "url": "https://genesis-world.readthedocs.io/"}],
        )
    )

    items.append(
        _checklist_item(
            id="genesis-world-pip",
            label="genesis-world package",
            status="ok" if _package_version("genesis-world") else "missing",
            detail=_package_version("genesis-world") or "Not installed",
            commands=["pip install genesis-world"],
        )
    )

    if world_root:
        items.append(
            _checklist_item(
                id="genesis-world-clone",
                label="genesis-world examples/",
                status="ok",
                detail=str(world_root),
            )
        )
    else:
        items.append(
            _checklist_item(
                id="genesis-world-clone",
                label="genesis-world examples/",
                status="missing",
                detail="Clone into repo root or set GENESIS_WORLD_ROOT",
                commands=[
                    "git clone https://github.com/Genesis-Embodied-AI/genesis-world.git",
                    f'$env:GENESIS_WORLD_ROOT = "{repo_root() / "genesis-world"}"',
                ],
                links=[{"label": "genesis-world", "url": "https://github.com/Genesis-Embodied-AI/genesis-world"}],
            )
        )

    if nyx_root:
        items.append(
            _checklist_item(
                id="genesis-nyx-clone",
                label="genesis-nyx examples/",
                status="ok",
                detail=str(nyx_root),
            )
        )
    else:
        items.append(
            _checklist_item(
                id="genesis-nyx-clone",
                label="genesis-nyx examples/",
                status="missing",
                detail="Required for Nyx rendering demos",
                commands=[
                    "git clone https://github.com/Genesis-Embodied-AI/genesis-nyx.git",
                    f'$env:GENESIS_NYX_ROOT = "{repo_root() / "genesis-nyx"}"',
                ],
                links=[{"label": "genesis-nyx", "url": "https://github.com/Genesis-Embodied-AI/genesis-nyx"}],
            )
        )

    pyuipc_ok, pyuipc_msg = optional_extra_available("pyuipc")
    items.append(
        _checklist_item(
            id="pyuipc",
            label="IPC solver (optional extra)",
            status="ok" if pyuipc_ok else "optional",
            detail=pyuipc_msg or "pip install pyuipc — Linux/Windows x86, NVIDIA GPU",
            commands=["pip install pyuipc"],
            links=[{"label": "genesis-world optional extras", "url": "https://github.com/Genesis-Embodied-AI/genesis-world#optional-extras"}],
        )
    )

    nyx_ok, nyx_msg = optional_extra_available("nyx")
    gpu = nvidia_gpu_hint()
    items.append(
        _checklist_item(
            id="gs-nyx-plugin",
            label="Nyx renderer (optional extra)",
            status="ok" if nyx_ok else "optional",
            detail=nyx_msg or "pip install gs-nyx-plugin — CUDA 12.9+, driver 575+",
            commands=["pip install gs-nyx-plugin"],
            links=[{"label": "genesis-nyx", "url": "https://github.com/Genesis-Embodied-AI/genesis-nyx"}],
        )
    )
    if not gpu.get("available"):
        items.append(
            _checklist_item(
                id="nvidia-gpu",
                label="NVIDIA GPU for Nyx/IPC",
                status="warning",
                detail=gpu.get("detail", "NVIDIA GPU recommended for Nyx and IPC demos"),
            )
        )

    items.append(
        _checklist_item(
            id="opengl",
            label="OpenGL 3+ for native viewer",
            status="info",
            detail="Genesis demos need a working GPU graphics driver. Blank white window that closes = OpenGL failed.",
            commands=[
                "Update AMD Software: Adrenalin → Check for Updates",
                "Windows Settings → System → Display → Graphics → add python.exe → High performance (AMD Radeon)",
                "Test in PowerShell: cd genesis-world && python examples/tutorials/mpm.py",
            ],
        )
    )

    items.append(
        _checklist_item(
            id="api-start",
            label="Start Buildables API",
            status="info",
            detail="Run from repo root without --reload on Windows",
            commands=[".\\scripts\\start-api.ps1"],
        )
    )

    return {
        "context": "environment",
        "title": "Environment setup for full Genesis catalogue",
        "summary": "Install genesis-world, clone example repos, optional pyuipc and gs-nyx-plugin.",
        "items": items,
    }


def _demo_requirements(scenario_id: str) -> dict[str, Any]:
    entry = get_showcase_entry(scenario_id)
    if entry is None:
        return {"context": "demo", "error": f"Unknown scenario: {scenario_id}", "items": []}

    described = describe_entry(entry)
    items: list[dict[str, Any]] = []

    if described["available"]:
        items.append(
            _checklist_item(
                id="script",
                label="Upstream script",
                status="ok",
                detail=described.get("script_path") or described["script_relpath"],
            )
        )
    else:
        for missing in described.get("missing", []):
            items.append(
                _checklist_item(
                    id=f"missing-{len(items)}",
                    label="Setup required",
                    status="missing",
                    detail=missing,
                )
            )

    if entry.optional_extra == "pyuipc":
        ok, msg = optional_extra_available("pyuipc")
        items.append(
            _checklist_item(
                id="pyuipc",
                label="pyuipc (IPC solver)",
                status="ok" if ok else "missing",
                detail=msg or "pip install pyuipc",
                commands=["pip install pyuipc"],
            )
        )
    elif entry.optional_extra == "nyx":
        ok, msg = optional_extra_available("nyx")
        items.append(
            _checklist_item(
                id="nyx",
                label="gs-nyx-plugin",
                status="ok" if ok else "missing",
                detail=msg or "pip install gs-nyx-plugin",
                commands=["pip install gs-nyx-plugin"],
            )
        )
        gpu = nvidia_gpu_hint()
        if not gpu.get("available"):
            items.append(
                _checklist_item(
                    id="gpu",
                    label="NVIDIA GPU",
                    status="warning",
                    detail=gpu.get("detail", "Nyx requires NVIDIA GPU with CUDA 12.9+"),
                )
            )

    items.append(
        _checklist_item(
            id="launch",
            label="Launch mode",
            status="info",
            detail="Opens in the Buildables web viewer via background recording.",
        )
    )

    return {
        "context": "demo",
        "scenario_id": scenario_id,
        "demo_name": entry.demo_name,
        "layer": entry.layer,
        "repo": entry.repo,
        "available": described["available"],
        "title": f"Requirements: {entry.demo_name}",
        "summary": described.get("script_relpath", ""),
        "items": items,
        "upstream_url": entry.upstream_url,
    }


def _custom_requirements(project_id: str) -> dict[str, Any]:
    pdir = project_dir(project_id)
    if not pdir.exists():
        return {"context": "custom", "error": f"Project not found: {project_id}", "items": []}

    validation_path = pdir / "import_validation.json"
    validation: dict[str, Any] = {}
    if validation_path.exists():
        validation = json.loads(validation_path.read_text(encoding="utf-8"))

    items: list[dict[str, Any]] = []

    items.append(
        _checklist_item(
            id="motion-file",
            label="Robot description (URDF or MJCF)",
            status="ok"
            if validation.get("robot_description", {}).get("urdf_found")
            or validation.get("robot_description", {}).get("mjcf_found")
            else "missing",
            detail="Upload URDF/MJCF in the Motion box when importing",
            links=[{"label": "Genesis asset formats", "url": "https://genesis-world.readthedocs.io/"}],
        )
    )

    missing_meshes = validation.get("geometry", {}).get("missing_mesh_references", [])
    items.append(
        _checklist_item(
            id="meshes",
            label="Mesh files referenced by URDF/MJCF",
            status="ok" if not missing_meshes else "missing",
            detail="All resolved" if not missing_meshes else f"Missing: {', '.join(missing_meshes[:8])}{'…' if len(missing_meshes) > 8 else ''}",
        )
    )

    missing_limits = validation.get("motion", {}).get("joint_limits_missing", [])
    items.append(
        _checklist_item(
            id="joint-limits",
            label="Joint limits on movable joints",
            status="ok" if not missing_limits else "warning",
            detail="All movable joints have limits"
            if not missing_limits
            else f"Missing limits on: {', '.join(missing_limits[:6])} — Genesis native viewer may fail",
        )
    )

    sim = validation.get("simulation_readiness", {})
    items.append(
        _checklist_item(
            id="passive",
            label="Passive rigid simulation",
            status="ok" if sim.get("passive") else "missing",
            detail="Required for Launch my robot (native viewer)",
        )
    )
    items.append(
        _checklist_item(
            id="joint-sim",
            label="Joint actuation",
            status="ok" if sim.get("joint") else "optional",
            detail="Movable joints detected" if sim.get("joint") else "Add revolute/prismatic joints for joint tests",
        )
    )
    items.append(
        _checklist_item(
            id="controlled",
            label="Controlled motion",
            status="ok" if sim.get("controlled") else "optional",
            detail=validation.get("sensors_control", {}).get("message", "Optional control script (.py)"),
        )
    )

    items.append(
        _checklist_item(
            id="scope",
            label="What custom uploads support today",
            status="info",
            detail="Rigid-body native viewer for your URDF/MJCF. MPM/cloth/Nyx catalogue demos use upstream scripts, not your upload.",
        )
    )

    items.append(
        _checklist_item(
            id="formats",
            label="Supported upload formats",
            status="info",
            detail="Motion: URDF, MJCF, XACRO, optional .py control script. Model: STEP, STL, OBJ, GLB, meshes.",
        )
    )

    return {
        "context": "custom",
        "project_id": project_id,
        "title": f"Upload requirements: {project_id}",
        "summary": "Files and metadata needed for your robot in Genesis native viewer.",
        "simulation_readiness": sim,
        "items": items,
    }


def build_upload_requirements(*, context: str, scenario_id: str | None = None, project_id: str | None = None) -> dict[str, Any]:
    if context == "environment":
        return _environment_requirements()
    if context == "demo":
        if not scenario_id:
            return {"context": "demo", "error": "scenario_id required for demo context", "items": []}
        return _demo_requirements(scenario_id)
    if context == "custom":
        if not project_id:
            return {
                "context": "custom",
                "title": "Upload requirements for custom projects",
                "summary": "Import a project first, then re-run this checker.",
                "items": [
                    _checklist_item(
                        id="import-first",
                        label="Import project",
                        status="missing",
                        detail="Use Import project with URDF/MJCF + mesh files in the My Projects tab.",
                    ),
                    *_environment_requirements()["items"][:3],
                ],
            }
        return _custom_requirements(project_id)
    return {"context": context, "error": f"Unknown context: {context}", "items": []}


def ensure_launch_project_id() -> str:
    """Minimal project used as anchor for showcase subprocess launches."""
    import json

    from app.services.project_store import create_project, load_manifest, save_manifest

    pid = "genesis-workbench"
    pdir = project_dir(pid)
    manifest_path = pdir / "manifest.buildables.physics.json"
    if not pdir.exists():
        create_project(project_name="Buildables Workbench", project_id=pid)

    # Repair legacy invalid enum values that break load_manifest().
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        changed = False
        if data.get("project_mode") not in ("default_demo", "imported_project"):
            data["project_mode"] = "default_demo"
            changed = True
        if data.get("project_type") not in (
            "robot_dog",
            "robot_arm",
            "wheeled_rover",
            "gripper",
            "drone",
            "mechanism",
            "imported_cad_assembly",
            "generic",
        ):
            data["project_type"] = "generic"
            changed = True
        if changed:
            manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    manifest = load_manifest(pid)
    if manifest.project_mode != "default_demo" or manifest.project_type != "generic":
        manifest.project_mode = "default_demo"
        manifest.project_type = "generic"
        save_manifest(pid, manifest)
    return pid
