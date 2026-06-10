# Engineering Report — IMU Sensor

**Run:** `agentic-report-imu` · **Project:** `default-robot-dog`
**Outcome:** Passed (passed)
**Generated:** 2026-06-08T09:01:29.982470+00:00

## Executive summary
IMU Sensor finished with outcome Passed (passed). Replay captured 1 frames. Telemetry recorded 20 samples.

## Plain language
I finished IMU Sensor. Outcome: passed.

Key results:
- Run status: completed
- Replay frames: 1
- Telemetry samples: 20

Limitations:
- IMU noise model and calibration were not validated against hardware.
- Results reflect Genesis rigid-body simulation fidelity — not manufacturing tolerances or real-world wear.

Recommended next step:
- Upload missing mesh files: URDF references meshes that were not found. Upload STL/OBJ files or export from STEP.

## Key metrics
- **Manifest status:** complete
- **Replay recorded:** True
- **Replay frames:** 5
- **Telemetry recorded:** True
- **Telemetry samples:** 20
- **Replay frames:** 1
- **Unique poses:** 1
- **Moving frames:** 1
- **Longest freeze run:** 1
- **Tracked objects:** 0
- **Recorder note:** repeated_transforms
- **IMU samples:** 20
- **Lin Acc Max:** 9.8
- **Ang Vel Max:** 0.1
- **Signal Changing:** True

## Time series
- **IMU telemetry:** 20 samples

## Limitations
- IMU noise model and calibration were not validated against hardware.
- Results reflect Genesis rigid-body simulation fidelity — not manufacturing tolerances or real-world wear.

## Recommendations
- **Upload missing mesh files** — URDF references meshes that were not found. Upload STL/OBJ files or export from STEP.
- **Ask Buildables CAD (not connected)** — Buildables CAD generation bridge is not connected yet. For now, upload a robot zip with meshes/, use STEP recovery, or accept skeleton fallback.
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