# Buildables Sim vs Genesis World

This document compares **Buildables Sim Sandbox** (this repo) with upstream **[Genesis World](https://github.com/Genesis-Embodied-AI/genesis-world)** and related **[genesis-nyx](https://github.com/Genesis-Embodied-AI/genesis-nyx)**.

## What Genesis World provides

Genesis is a full simulation **platform** with four layers ([genesis-world README](https://github.com/Genesis-Embodied-AI/genesis-world#what-is-genesis-world)):

| Layer | What you get in upstream |
|-------|--------------------------|
| **Physics** | Rigid, FEM, MPM, SPH, PBD, uIPC, couplers, SAP — unified multi-physics |
| **Render** | Nyx (path-traced), Luisa, Pyrender as camera sensors |
| **Simulation interface** | URDF/MJCF/USD loaders, sensors, controllers, parallel envs, built-in GUI/ImGui |
| **Compiler** | Quadrants (CUDA/Metal/Vulkan/CPU) bundled with Genesis |

The upstream **catalogue** runs as standalone Python scripts under `examples/` (physics, rendering, sensors, GUI). Optional extras:

- **IPC / cloth teleop:** `pip install pyuipc` (Linux/Windows x86, NVIDIA GPU)
- **Nyx renderer:** `pip install gs-nyx-plugin` — see [genesis-nyx](https://github.com/Genesis-Embodied-AI/genesis-nyx) (CUDA 12.9+, driver 575+)

Each demo opens Genesis's **native viewer** (`show_viewer=True`) with full solver visuals.

## What Buildables adds (not in genesis-world repo)

| Feature | Description |
|---------|-------------|
| **Web workbench** | Next.js UI: resizable sidebars, inspector, test lab, timeline replay |
| **Manifest-driven projects** | Versioned `manifest.buildables.physics.json`, save/load, robot-dog demo pack |
| **FastAPI orchestration** | REST API for run-scene, tests, import, interactive keyboard segments |
| **Default robot dog MVP** | Zero-upload demo with bundled URDF/STEP/meshes under `sim-data/` |
| **Import workflow** | Two-box upload: motion (URDF/MJCF) + model (STEP/STL/meshes) |
| **Genesis Workbench (Next Interface)** | Dedicated `/genesis` UI: full catalogue native launch, optional extras status, **What do I need?** checker, custom URDF import — see [`GENESIS_WORKBENCH.md`](GENESIS_WORKBENCH.md) |
| **Test suite + metrics** | Pass/fail tests, `state_timeseries.json`, replay in Three.js viewport |
| **Buildables-specific controls** | WASD remote control, payload/sensor metadata, project tree |

## What Buildables does **not** have (yet) vs Genesis

| Genesis capability | Status in Buildables |
|--------------------|----------------------|
| **Native Genesis viewer in browser** | Uses Three.js preview + optional **Native viewer** button (separate OS window) |
| **MPM / SPH / PBD / smoke / cloth demos** | **Genesis Workbench** launches upstream scripts natively; Buildables `/` workbench still runs robot-dog profile for Run scenario |
| **Nyx path-traced renders in UI** | Launch via **Genesis Workbench → Nyx** section (native window); not embedded in Three.js |
| **IPC (pyuipc) cloth teleop** | Launch via **Genesis Workbench** when `pyuipc` installed |
| **ImGui joint GUI, mesh picker, mouse interaction** | Not in web UI |
| **Parallel / heterogeneous envs** | Not exposed |
| **Domain randomization, batched IK, drone, worm** | Catalog entries only |
| **Full sensor artifact export** (lidar clouds, tactile grids) | Partial metrics only |
| **USD asset pipeline** | URDF/MJCF/STEP/STL focus |
| **Exact upstream example parity** | Use **Next Interface → Genesis Workbench** (`/genesis`) to launch `genesis-world/examples/*.py` and genesis-nyx examples |

## Why catalogue demos differ on Buildables `/` vs Genesis Workbench

1. **Buildables workbench (`/`)** — Three.js viewport replays robot **state timeseries**. Top bar **Run** uses your manifest robot profile, not upstream Franka/cloth scripts.

2. **Genesis Workbench (`/genesis`)** — Click **Next Interface**. Launches upstream example scripts in **native OS windows** with full solver visuals (MPM, Nyx, IPC, etc.).

3. **Optional backends** — Nyx and IPC need extra installs ([genesis-nyx](https://github.com/Genesis-Embodied-AI/genesis-nyx), `pyuipc`). Use **What do I need?** in Genesis Workbench.

## How to get closer to genesis-world behavior

| Goal | Action |
|------|--------|
| Full genesis-world + nyx catalogue | **Next Interface** → [`/genesis`](GENESIS_WORKBENCH.md) → Launch native demo |
| See native Genesis viewer (your robot) | Genesis Workbench **My Projects** or Buildables **Native viewer** |
| Nyx renders | Genesis Workbench → Nyx section + `pip install gs-nyx-plugin` |
| MPM/cloth/SPH demos | Genesis Workbench → Physics section |
| Robot dog in Buildables web replay | **Load Demo → Robot Dog Demo** on `/` workbench |

## Quick start (fix "Cannot reach API")

```powershell
# Terminal 1 — API (repo root)
uvicorn main:app --app-dir apps/api --host 127.0.0.1 --port 8000

# Terminal 2 — Web
npm run dev:web
```

Avoid `--reload` while running Genesis simulations on Windows (LLVM threading).
