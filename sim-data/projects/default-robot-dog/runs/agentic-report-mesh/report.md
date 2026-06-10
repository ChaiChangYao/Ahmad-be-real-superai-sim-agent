# Engineering Report — Joint Sweep

**Run:** `agentic-report-mesh` · **Project:** `default-robot-dog`
**Outcome:** Failed (failed)
**Generated:** 2026-06-08T09:01:16.916002+00:00

## Executive summary
Joint Sweep finished with outcome Failed (failed). 1 issue(s) noted in logs.

## Plain language
I finished Joint Sweep. Outcome: failed.

Key results:
- Run status: failed
- Replay frames: 0

Limitations:
- No stress, buckling, or fatigue analysis was performed.
- Results reflect Genesis rigid-body simulation fidelity — not manufacturing tolerances or real-world wear.

Recommended next step:
- Upload missing mesh files: URDF references meshes that were not found. Upload STL/OBJ files or export from STEP.

## Key metrics
- **Manifest status:** failed
- **Replay recorded:** False
- **Replay frames:** 0
- **Telemetry recorded:** False
- **Replay frames:** 0

## Detected issues
### Missing mesh or asset file (error)
Log pattern detected: missing asset.
- *Suggested fix:* Upload the missing mesh files or map STEP parts to URDF paths.

## Limitations
- No stress, buckling, or fatigue analysis was performed.
- Results reflect Genesis rigid-body simulation fidelity — not manufacturing tolerances or real-world wear.

## Recommendations
- **Upload missing mesh files** — URDF references meshes that were not found. Upload STL/OBJ files or export from STEP.
- **Ask Buildables CAD (not connected)** — Buildables CAD generation bridge is not connected yet. For now, upload a robot zip with meshes/, use STEP recovery, or accept skeleton fallback.
- **Re-run after fixing blockers** — Address detected issues, then run the same test again.
- **Try Gravity Stability** — Drop or settle model under gravity; report stability and contact summary.
- **Try IMU Sensor** — Simulate IMU on attach link; record linear acceleration and angular velocity.

## Suggested next tests
- `gravity_stability`
- `imu_sensor`
- `contact_force`
- `depth_camera`
- `thermal_grid_readiness`

## Disclaimer
This report is generated from recorded simulation artifacts. It describes what was observed in the run — not guaranteed real-world performance.