# Genesis Workbench (Next Interface)

The **Genesis Workbench** is a dedicated UI for full [genesis-world](https://github.com/Genesis-Embodied-AI/genesis-world) catalogue parity and [genesis-nyx](https://github.com/Genesis-Embodied-AI/genesis-nyx) rendering demos. It is separate from the Buildables robot-dog workbench.

## Open it

1. Start the API: `.\scripts\start-api.ps1`
2. Start the web UI: `npm run dev:web`
3. On the Buildables workbench top bar, click **Next Interface** → `/genesis`
4. Return via **Buildables Workbench** in the Genesis header

## What it includes

| Section | Source | Launch |
|---------|--------|--------|
| **Physics** | genesis-world `examples/` | Native Genesis viewer window |
| **Rendering (world)** | genesis-world camera demos | Native viewer |
| **Nyx** | genesis-nyx `examples/` | Native Nyx path-traced viewer |
| **Simulation Interface** | sensors, GUI, controllers, drone, worm | Native viewer |
| **My Projects** | Your URDF/MJCF upload | Native viewer for your robot |

Simulations run in **native OS windows** (upstream scripts with `show_viewer=True`), not in the Buildables Three.js viewport.

## Optional extras (from genesis-world README)

| Extra | Install | Used for |
|-------|---------|----------|
| **IPC solver** | `pip install pyuipc` | IPC cloth/robot teleop demos (Linux/Windows x86, NVIDIA GPU) |
| **Nyx renderer** | `pip install gs-nyx-plugin` | All genesis-nyx examples ([requirements](https://github.com/Genesis-Embodied-AI/genesis-nyx): CUDA 12.9+, driver 575+) |
| **Quadrants** | Bundled with genesis-world | No separate install |

Clone example repos if pip omits `examples/`:

```powershell
git clone https://github.com/Genesis-Embodied-AI/genesis-world.git
git clone https://github.com/Genesis-Embodied-AI/genesis-nyx.git
```

Buildables auto-detects clones in the repo root (`genesis-world/`, `genesis-nyx/`).

## What do I need?

The **What do I need?** button opens a checklist for three contexts:

| Context | When | Shows |
|---------|------|--------|
| **Environment** | Header button (always) | Python, PyTorch, clones, optional extras, API start |
| **Demo** | Selected catalogue item | Script path, missing setup, pyuipc/nyx/GPU requirements |
| **Custom** | My Projects tab | URDF/MJCF, meshes, joint limits, passive sim readiness |

## Custom uploads (My Projects)

Upload:

- **Motion:** URDF, MJCF, XACRO, optional `.py` control script
- **Model:** STL, OBJ, GLB, STEP, textures

When validation passes **passive simulation**, use **Launch my robot (native)**.

Custom URDF projects support **rigid native viewer** only. MPM/cloth/Nyx catalogue demos remain upstream scripts.

## API

| Method | Path |
|--------|------|
| GET | `/genesis/workbench/readiness` |
| GET | `/genesis/workbench/upload-requirements?context=environment\|demo\|custom` |
| GET | `/genesis/workbench/launch-project` |
| POST | `/projects/{id}/genesis/showcase/{scenario_id}/launch` |
| POST | `/projects/{id}/genesis/native-viewer/run` |

See also [`GENESIS_SHOWCASE_RUNNER.md`](GENESIS_SHOWCASE_RUNNER.md).
