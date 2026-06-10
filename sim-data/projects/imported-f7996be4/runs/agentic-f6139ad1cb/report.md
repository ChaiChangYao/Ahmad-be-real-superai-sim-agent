# Engineering Report — IMU Sensor

**Run:** `agentic-f6139ad1cb` · **Project:** `imported-f7996be4`
**Outcome:** Failed (failed)
**Generated:** 2026-06-09T08:29:20.260373+00:00

## Executive summary
IMU Sensor finished with outcome Failed (failed). 1 issue(s) noted in logs.

## Plain language
I finished IMU Sensor. Outcome: failed.

Key results:
- Run status: failed
- Replay frames: 0

Limitations:
- IMU noise model and calibration were not validated against hardware.
- Results reflect Genesis rigid-body simulation fidelity — not manufacturing tolerances or real-world wear.

Recommended next step:
- Re-run after fixing blockers: Address detected issues, then run the same test again.

## Key metrics
- **Manifest status:** failed
- **Replay recorded:** False
- **Replay frames:** 0
- **Telemetry recorded:** False
- **Telemetry samples:** 0
- **Replay frames:** 0

## Detected issues
### Run failure (error)
[agentic_runtime] Run failed: Scene.add_sensor() got an unexpected keyword argument 'update_rate'
- *Suggested fix:* Review run logs and verify project assets.

## Limitations
- IMU noise model and calibration were not validated against hardware.
- Results reflect Genesis rigid-body simulation fidelity — not manufacturing tolerances or real-world wear.

## Recommendations
- **Re-run after fixing blockers** — Address detected issues, then run the same test again.
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