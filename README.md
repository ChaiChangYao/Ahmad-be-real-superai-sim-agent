# Buildables Sim Sandbox

Standalone localhost robotics simulation MVP focused on pre-procurement behavior validation.

The default demo is `default-robot-dog` and works without any uploaded CAD assets.

## Current Status
- Real Genesis import/init/scene-step execution path is required for simulation runs.
- Default robot dog project includes built-in manifest, scenarios, control scripts, and collision shell.
- Frontend supports manifest editing, save/dirty state, scenario run, and keyboard command-stepped interaction.
- Uploading STEP/GLB/STL/OBJ remains optional advanced workflow.
- No auth, no database, no cloud integrations.

## Windows Setup
```powershell
.\tools\setup_windows.ps1
```

Manual setup:
```powershell
npm install
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r apps/api/requirements.txt
```

## Start App
Backend (terminal 1):
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --app-dir apps/api --host 127.0.0.1 --port 8000
```

Verify API (not the web UI):
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Frontend (terminal 2 — separate window):
```powershell
npm run dev
```

Open the **web app** at [http://localhost:3000](http://localhost:3000).

Note: `http://127.0.0.1:8000` is the **API only** (JSON). It is normal if the root URL shows a JSON message rather than a web page.

## Default Demo (No Uploads)
1. Open app.
2. Click `Load Default Robot Dog Demo` (top bar).
3. Start interactive mode.
4. Focus viewport and use keyboard:
   - `W/A/S/D`: move/turn
   - `Space`: jump
   - `R`: reset
   - `Esc`: emergency stop
5. Run scenarios from selector and inspect logs/results/metrics.

## Imported Project Mode (URDF/MJCF + Meshes)
1. Click `Import Project`.
2. Upload:
   - URDF or MJCF/XML
   - visual/collision meshes (GLB/GLTF/OBJ/STL, optional STEP source CAD)
   - optional control script/metadata files
3. Review `Import Validation`.
4. Click `Load Imported Project`.
5. Active project switches to imported mode; viewport and tests target imported mechanism.

### Run imported project tests
- Passive gravity: `POST /projects/{project_id}/tests/passive-gravity/run`
- Joint sweep: `POST /projects/{project_id}/tests/joint-sweep/run`
- Mechanism motion: `POST /projects/{project_id}/tests/mechanism-motion/run`
- Control script: `POST /projects/{project_id}/tests/control-script/run`

### Verify active project and Genesis usage
```powershell
Invoke-RestMethod http://localhost:8000/projects/active
Invoke-RestMethod http://localhost:8000/projects/{project_id}/robot-description
Invoke-RestMethod http://localhost:8000/genesis/status
```

Default robot dog is fallback demo only. Imported project mode overrides default scene until you explicitly switch back.

## Viewport QA Checklist
1. Open app.
2. Click `Load Default Robot Dog Demo`.
3. Confirm full robot dog is visible in the center viewport.
4. Confirm torso, front sensor panel, all four legs, and all four feet are visible.
5. Confirm floor grid is visible under the robot.
6. Left-drag to orbit camera.
7. Scroll wheel to zoom in/out.
8. Right-drag (or middle-drag) to pan.
9. Click `Reset Camera` in viewport HUD and confirm framing resets.
10. Press `W/A/S/D` and confirm visual preview movement.
11. Press `Space` and confirm jump animation.
12. Press `R` and confirm pose/position reset.
13. Confirm bottom drawer is compact and tabbed.
14. Confirm Test Results and Metrics remain compact when empty.

## Verify Genesis Is Really Stepping
Basic checks:
```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/genesis/status
```

Real simulation checks:
```powershell
python apps/api/app/scripts/run_robot_dog_genesis_smoke_test.py
python apps/api/app/scripts/run_default_robot_dog_genesis_smoke_test.py
python apps/api/app/scripts/run_default_robot_dog_keyboard_smoke_test.py
python apps/api/app/scripts/run_default_robot_dog_scenario_suite.py
python apps/api/app/scripts/api_smoke_test.py
```

Genesis native example checks:
```powershell
python apps/api/app/scripts/genesis_examples/00_check_genesis_install.py
python apps/api/app/scripts/genesis_examples/01_plane_and_box_drop.py
python apps/api/app/scripts/genesis_examples/02_load_urdf_passive_gravity.py --urdf path/to/model.urdf
python apps/api/app/scripts/genesis_examples/03_load_mjcf_robot.py --mjcf path/to/model.xml
python apps/api/app/scripts/genesis_examples/04_joint_slider_control.py --urdf path/to/model.urdf
python apps/api/app/scripts/genesis_examples/05_apply_force_and_topple.py
python apps/api/app/scripts/genesis_examples/06_payload_load_test.py --urdf path/to/model.urdf --payload-mass-kg 8
python apps/api/app/scripts/genesis_examples/07_contact_collision_test.py
python apps/api/app/scripts/genesis_examples/08_sensor_test.py --urdf path/to/model.urdf
python apps/api/app/scripts/genesis_examples/09_render_video_test.py
python apps/api/app/scripts/genesis_examples/10_soft_deformation_or_cable_test.py
python apps/api/app/scripts/verify_true_genesis_pipeline.py
```

## Fix port 8000 already in use

If the backend fails to start because port 8000 is already in use:

```powershell
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
uvicorn main:app --reload --app-dir apps/api --host 127.0.0.1 --port 8000
```

Only kill the PID bound to `127.0.0.1:8000`. If multiple uvicorn processes exist, kill each stale PID before restarting.

## Fix port 3000 already in use (frontend stuck or 500 error)

If `npm run dev:web` fails with `EADDRINUSE` or the browser shows a blank/loading page forever:

```powershell
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F
npm run dev:web
```

Then open [http://localhost:3000](http://localhost:3000) again.

Other checks:
```powershell
npm run build:web
python -m compileall apps/api
python tools/check_no_forbidden_engines.py
```

## What Is Real vs Limited
Real now:
- Genesis availability gating and blocking errors
- Scene stepping loop for scenario and interactive command segments
- Manifest versioning and run linkage (`manifest_version_used`)
- State timeseries artifact generation and replay-ready payloads
- Default no-upload robot dog project path

Still limited:
- Genesis-native entity articulation fidelity depends on installed Genesis API capabilities
- Sensor/wire/component-fit checks include derived geometry metrics
- CAD STEP conversion quality depends on local converter tooling availability

## Optional CAD Import Path
- Upload STEP/STL/OBJ/GLB.
- STEP is stored as source CAD.
- Visual mesh and collision primitives are generated/mapped into manifest.
- Simulation runs from manifest + collision shell + robot description metadata.

## Disclaimer
This simulation is for pre-procurement robotics behavior validation and rapid iteration. It is not certified final FEA, thermal, electrical, or safety validation.
