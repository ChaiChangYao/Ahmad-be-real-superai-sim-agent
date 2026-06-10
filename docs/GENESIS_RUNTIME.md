# Genesis Runtime

## Runtime Flow
1. Load saved manifest from `sim-data/projects/{project_id}/manifest.buildables.physics.json`.
2. Initialize Genesis (`genesis_runtime.initialize()`).
3. Create scene + ground.
4. Convert manifest into scene-ready links/joints/actuators.
5. Step simulation in fixed `dt` increments.
6. Export metrics, logs, and `state_timeseries`.
7. Save run artifacts in `sim-data/projects/{project_id}/runs/{run_id}/`.

## Manifest to Genesis
- Visual geometry comes from project visual assets/procedural definitions.
- Physics uses simplified collision primitives from manifest.
- Robot description paths (`URDF/MJCF`) are preserved in run artifacts.

## Metrics Sources
- `genesis_state`:
  - body height
  - pitch/roll/yaw extrema
  - forward distance
  - joint position ranges
  - foot contact ratio
- `derived_from_genesis_state`:
  - fall detection
  - center of mass approximation
  - sensor clearance estimate
- `derived_from_manifest_and_genesis_state`:
  - torque margin
  - battery CoM height influence

## Failure Behavior
- If Genesis import/init/scene creation fails, simulation endpoints return a blocking error.
- No alternate simulator path is used.
