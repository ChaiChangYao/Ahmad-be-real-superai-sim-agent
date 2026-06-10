# Genesis patterns (reference-only)

Adapted from `external/references/genesis-world` examples — not vendored into runtime.

## Scene bootstrap (web mode)

- `gs.init(backend=gs.cpu, logging_level="warning")`
- `gs.Scene(show_viewer=False, sim_options=gs.options.SimOptions(dt=...))`
- Floor via `scene.add_entity(gs.morphs.Plane())`
- Robot via `scene.add_entity(gs.morphs.URDF/MJCF(file=...))`
- `scene.build()` before stepping

## Sensors

- IMU: `gs.sensors.IMU` attached to entity link indices
- Contact: collision-enabled bodies + force readback hooks
- Depth: render path without `cv2.imshow` or native viewer

## Headless / web rules

- No `show_viewer=True`
- No `matplotlib.pyplot.show()`
- No `cv2.imshow`
- Outputs written under project `generated/runs/<script_id>/`

## Templates

Each test maps 1:1 to a Jinja template in `apps/api/app/services/agentic/templates/`.
Selection is driven by `test_id` + `fallback_mode` from preflight — never catalogue demo IDs.
