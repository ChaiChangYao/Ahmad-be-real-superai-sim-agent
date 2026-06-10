# Engineering Report — IMU Sensor

**Run:** `agentic-ae69df4ace` · **Project:** `imported-f7996be4`
**Outcome:** Passed (passed)
**Generated:** 2026-06-09T08:49:04.467049+00:00

## Executive summary
IMU Sensor finished with outcome Passed (passed). Replay captured 2095 frames. Telemetry recorded 400 samples. 1 issue(s) noted in logs.

## Plain language
I finished IMU Sensor. Outcome: passed.

Key results:
- Run status: completed
- Replay frames: 2095
- Telemetry samples: 400

Limitations:
- IMU noise model and calibration were not validated against hardware.
- Results reflect Genesis rigid-body simulation fidelity — not manufacturing tolerances or real-world wear.

Recommended next step:
- Try Gravity Stability: Drop or settle model under gravity; report stability and contact summary.

## Key metrics
- **Manifest status:** complete
- **Replay recorded:** True
- **Replay frames:** 2095
- **Telemetry recorded:** True
- **Telemetry samples:** 400
- **Replay frames:** 2095
- **Unique poses:** 2095
- **Moving frames:** 1592
- **Longest freeze run:** 209
- **Tracked objects:** 14
- **Recorder note:** sparse_motion_phases
- **IMU samples:** 400
- **Lin Acc Max:** 0.0
- **Ang Vel Max:** 3.99
- **Signal Changing:** True

## Time series
- **IMU telemetry:** 400 samples

## Detected issues
### Run failure (error)
[showcase_launcher] Wrote 2095 replay frames (final, v14) · raw=400 unique_poses=400 preview=2095 · 14 objects (13 robot links) to C:\Users\user\Physics Sim Buildables\PhysicsSimBuildables\sim-data\projects\imported-f7996be4\runs\agentic-ae69df4ace\state_timeseries.json
- *Suggested fix:* Review run logs and verify project assets.

## Limitations
- IMU noise model and calibration were not validated against hardware.
- Results reflect Genesis rigid-body simulation fidelity — not manufacturing tolerances or real-world wear.

## Recommendations
- **Try Gravity Stability** — Drop or settle model under gravity; report stability and contact summary.
- **Try Joint Sweep** — Sweep movable joints through limits; detect collisions and range issues.

## Suggested next tests
- `gravity_stability`
- `joint_sweep`
- `contact_force`
- `depth_camera`
- `thermal_grid_readiness`

## Disclaimer
This report is generated from recorded simulation artifacts. It describes what was observed in the run — not guaranteed real-world performance.