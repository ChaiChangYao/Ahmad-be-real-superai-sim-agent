# Genesis Native Runtime

This project now includes a Genesis-native runtime path in `apps/api/app/services/genesis_native/`.

## Runtime Flow

1. `import genesis as gs`
2. `gs.init(backend=...)`
3. `scene = gs.Scene(sim_options=gs.options.SimOptions(dt=...), show_viewer=...)`
4. `scene.add_entity(gs.morphs.Plane())`
5. `scene.add_entity(gs.morphs.URDF(...))` or `gs.morphs.MJCF(...)` or `gs.morphs.Mesh(...)`
6. `scene.build()`
7. For each timestep:
   - apply controls/forces where configured
   - `scene.step()`
   - collect state (`get_pos`, `get_quat`, `get_dofs_position`, contacts)
8. Save artifacts:
   - `state_timeseries.json`
   - `metrics.json`
   - `logs.txt`
   - `result.json`

## Modes

- Native debug mode: `show_viewer=True`
- Web replay mode: `show_viewer=False`

The backend Genesis step loop is the simulation source of truth.
