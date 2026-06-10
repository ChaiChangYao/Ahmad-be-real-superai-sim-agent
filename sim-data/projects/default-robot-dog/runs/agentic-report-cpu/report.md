# Engineering Report — Gravity Stability

**Run:** `agentic-report-cpu` · **Project:** `default-robot-dog`
**Outcome:** Passed (passed)
**Generated:** 2026-06-08T09:01:53.887927+00:00

## Executive summary
Gravity Stability finished with outcome Passed (passed). Replay captured 2 frames. 2 issue(s) noted in logs.

## Plain language
I finished Gravity Stability. Outcome: passed.

Key results:
- Run status: completed
- Replay frames: 2

Limitations:
- No stress, buckling, or fatigue analysis was performed.
- Results reflect Genesis rigid-body simulation fidelity — not manufacturing tolerances or real-world wear.

Recommended next step:
- Upload missing mesh files: URDF references meshes that were not found. Upload STL/OBJ files or export from STEP.

## Key metrics
- **Manifest status:** complete
- **Replay recorded:** True
- **Replay frames:** 8
- **Telemetry recorded:** False
- **Replay frames:** 2
- **Unique poses:** 2
- **Moving frames:** 2
- **Longest freeze run:** 1
- **Tracked objects:** 1
- **Recorder note:** repeated_transforms

## Detected issues
### CPU fallback in use (warning)
Log pattern detected: cpu fallback.
- *Suggested fix:* Simulation ran on CPU — slower but not necessarily a physics failure.
### Run failure (error)
Genesis using CPU fallback — no CUDA device found
- *Suggested fix:* Review run logs and verify project assets.

## Limitations
- No stress, buckling, or fatigue analysis was performed.
- Results reflect Genesis rigid-body simulation fidelity — not manufacturing tolerances or real-world wear.

## Recommendations
- **Upload missing mesh files** — URDF references meshes that were not found. Upload STL/OBJ files or export from STEP.
- **Ask Buildables CAD (not connected)** — Buildables CAD generation bridge is not connected yet. For now, upload a robot zip with meshes/, use STEP recovery, or accept skeleton fallback.
- **CPU execution note** — Run used CPU fallback — expect slower performance, not necessarily incorrect physics.
- **Try Joint Sweep** — Sweep movable joints through limits; detect collisions and range issues.
- **Try IMU Sensor** — Simulate IMU on attach link; record linear acceleration and angular velocity.

## Suggested next tests
- `joint_sweep`
- `imu_sensor`
- `contact_force`
- `depth_camera`
- `thermal_grid_readiness`

## Disclaimer
This report is generated from recorded simulation artifacts. It describes what was observed in the run — not guaranteed real-world performance.