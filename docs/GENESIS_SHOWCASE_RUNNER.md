# Genesis showcase example script runner

Buildables can launch **true upstream Genesis demos** from the sidebar **Showcase** tab. Each catalogue item runs the matching script from [genesis-world](https://github.com/Genesis-Embodied-AI/genesis-world) or [genesis-nyx](https://github.com/Genesis-Embodied-AI/genesis-nyx) in a **separate Python process** with the native Genesis/Nyx viewer (`show_viewer=True` in those scripts).

This is different from **Run scenario** in the top bar, which executes your robot-dog project profile inside Buildables (web replay + metrics).

## Setup

1. **Install Genesis** in the same Python env as the Buildables API (see project README / `docs/DEFAULT_ROBOT_DOG.md`).

2. **Clone upstream repos** (pip installs often omit `examples/`). If you clone into the repo root (`genesis-world/`, `genesis-nyx/`), Buildables auto-detects them — no env vars required.

   ```powershell
   git clone https://github.com/Genesis-Embodied-AI/genesis-world.git
   git clone https://github.com/Genesis-Embodied-AI/genesis-nyx.git
   ```

   Or set paths explicitly:

   ```powershell
   $env:GENESIS_WORLD_ROOT = "C:\path\to\genesis-world"
   $env:GENESIS_NYX_ROOT = "C:\path\to\genesis-nyx"
   ```

3. **Optional extras**

   - Nyx rendering demos: `pip install gs-nyx-plugin` (CUDA 12.9+, driver 575+)
   - IPC demos: `pip install pyuipc`

4. **Start the API without `--reload` on Windows** (avoids Genesis/Taichi threading issues):

   ```powershell
   .\scripts\start-api.ps1
   ```

   Or manually:

   ```powershell
   uvicorn main:app --app-dir apps/api --host 127.0.0.1 --port 8000
   ```

   **Restart the API** after pulling Buildables changes — an old process on port 8000 will miss new routes and cause 404/timeouts in the UI.

## Using the UI

1. Open **Showcase** in the workbench sidebar.
2. Pick a `[Genesis …]` scenario.
3. Click **Launch native demo** when the badge shows **native ready**.
4. A native viewer window opens in a subprocess. Close the viewer to finish.

Launch metadata is stored under `sim-data/projects/<project_id>/runs/showcase-<id>/launch.json`.

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/genesis/showcase/catalog` | List catalogue entries + script availability on this machine |
| POST | `/projects/{id}/genesis/showcase/{scenario_id}/launch` | Start upstream example script |
| GET | `/projects/{id}/genesis/showcase/launch/{launch_id}` | Poll launch status |

## Troubleshooting

- **setup needed** badge — set `GENESIS_WORLD_ROOT` / `GENESIS_NYX_ROOT` and verify the script path exists under `examples/`.
- **404 on launch** — restart the API after pulling Buildables changes; an old process may not expose the new routes.
- **Nyx / IPC errors** — install the optional extra shown in the scenario detail panel.
- **llvm_context / main_thread_id** — use a single API worker, avoid `--reload`, and ensure Genesis init uses the shared runtime lock (see `apps/api/app/services/genesis_native/genesis_runtime.py`).
