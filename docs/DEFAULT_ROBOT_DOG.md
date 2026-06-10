# Default Robot Dog

The default robot dog demo works with **zero uploads**. All physics assets ship inside the repo.

## Project Path
- `sim-data/projects/default-robot-dog/`

## Asset Pack
- **Bundled URDF (Genesis physics):**
  - `assets/imported/robot_dog_buildables_demo.urdf`
  - `assets/imported/meshes/collision/*.stl`
- **Bundled STEP (CAD source, visual reference):**
  - `assets/imported/robot_dog_buildables_demo.step`
- **Procedural web preview:**
  - `assets/visual/generated_robot_dog_parts.json`
- **Generated fallbacks:**
  - `generated/robot_description/default_robot_dog.urdf`
  - `generated/robot_description/default_robot_dog.mjcf`
  - `generated/robot_description/genesis_physics.urdf`

On first load, `POST /projects/default-robot-dog/load` rewires the manifest to bundled paths. Optional: files in `%USERPROFILE%\Downloads\` can refresh the bundled copy.

## Load Options (UI)
| Menu item | What it does |
|-----------|----------------|
| **Robot Dog Demo** | Loads `default-robot-dog` — no upload required |
| **My Robot Dog (Downloads URDF)** | Creates a separate `imported-*` project from Downloads |

## Controls
- `W` forward · `A` turn left · `S` backward · `D` turn right
- `Space` jump · `R` reset · `Esc` emergency stop

## Scenarios
stand_balance, walk_forward, payload_carry, joint_sweep_collision, sensor_visibility, wire_route, component_fit, and Genesis showcase scenarios.

## Verification
```powershell
python apps/api/app/scripts/run_default_robot_dog_genesis_smoke_test.py
python apps/api/app/scripts/run_robot_dog_genesis_smoke_test.py
python apps/api/app/scripts/run_default_robot_dog_keyboard_smoke_test.py
python apps/api/app/scripts/run_default_robot_dog_scenario_suite.py
python apps/api/app/scripts/api_smoke_test.py
```

Expected: `genesis_used=true`, `mocked=false`, `step_count > 0`.

## Backend start (Windows)
```powershell
uvicorn main:app --app-dir apps/api --host 127.0.0.1 --port 8000
```
Avoid `--reload` during Genesis runs (Taichi/LLVM threading).
