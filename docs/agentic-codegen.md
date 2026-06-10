# Agentic Code Generation (Part 3)

## Why templates exist

Genesis remains the physics engine. Buildables generates **inspectable, typed** simulation scripts from:

- Uploaded project files and inspection results
- Selected `test_id` from the test requirement matrix
- User parameters and safe defaults
- Explicit fallback modes (`skeleton`, `static_mesh`)

Templates prevent catalogue hardcoding (no default Franka arm, no implicit telemetry panels).

## Template registry

`apps/api/app/services/agentic/codegen/template_registry.py` maps `test_id` + `fallback_mode` → `.py.j2` files under `apps/api/app/services/agentic/templates/`.

| test_id | Template | Notes |
|---------|----------|-------|
| `gravity_stability` | `gravity_stability.py.j2` | Robot or mesh |
| `joint_sweep` | `joint_sweep.py.j2` | Full visual |
| `joint_sweep` + `skeleton` | `skeleton_preview.py.j2` | Mesh-free URDF |
| `imu_sensor` | `imu_sensor.py.j2` | IMU telemetry only |
| `contact_force` | `contact_force.py.j2` | Link names from inspection |
| `depth_camera` | `depth_camera.py.j2` | No OpenCV windows |
| `thermal_grid_readiness` | `temperature_grid.py.j2` | Demo field — not engineering-valid |
| `static_mesh_preview` | `static_mesh_preview.py.j2` | STEP/STL only |
| `fea_readiness` / `cfd_readiness` | — | Blocked — readiness only |

## Context schema

`GenesisScriptContext` (see `codegen/schemas.py`) is written as `<script_id>.context.json` beside the generated script. Scripts load this at runtime — no hardcoded absolute paths.

## Safety rules

`codegen/safety.py` AST-validates generated scripts:

- Allowed imports: `os`, `sys`, `json`, `math`, `pathlib`, `traceback`, `time`, `numpy`, `genesis`, `app.*` runtime helpers
- Banned: `subprocess`, `socket`, `requests`, `eval`, `exec`, `plt.show`, `cv2.imshow`
- Outputs only under project `generated/` folders

## Generated script lifecycle

1. `POST /api/projects/{id}/generate-script` → `CodeGenResult`
2. Script: `sim-data/projects/{id}/generated/scripts/{script_id}.py`
3. Context: `.../{script_id}.context.json`
4. Run output (Part 4): `.../generated/runs/{script_id}/`
5. User inspects code in **Generated Script Viewer** before run

## Runtime helpers

Generated scripts call `app.services.agentic.runtime.*` — not duplicated Genesis boilerplate.

## Adding a new test template

1. Add `SimulationTestSpec` in `test_requirements.py`
2. Register `GenesisTemplateSpec` in `template_registry.py`
3. Create `templates/<name>.py.j2`
4. Extend `template_context.py` if new config blocks are needed
5. Add verification case in `verify_codegen.py`

## What not to hardcode

- Robot model names (Franka, Go2, Panda)
- Joint names
- Sensor attach links (derive from URDF + user choice)
- Telemetry panels for non-sensor tests
- FEA/CFD physics scripts without real solver support
