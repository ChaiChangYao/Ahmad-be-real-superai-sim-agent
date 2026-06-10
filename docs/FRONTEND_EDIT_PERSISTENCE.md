# Frontend Edit Persistence

## Flow
1. Inspector edits mutate one canonical manifest state in frontend store.
2. Store marks manifest as `Unsaved changes`.
3. `Save Manifest` validates and persists to backend.
4. Backend increments `manifest.version` and snapshots history.
5. Simulation run uses saved manifest from disk.
6. Result includes `manifest_version_used`.

## Saved State Indicators
- `Unsaved changes`
- `Saved`
- `Validation errors`
- `Last saved` timestamp

## Change-After-Run Warning
If current manifest version differs from `manifest_version_used`, UI shows:
- `Current manifest has changed since last run.`

## Auto-Guess Joints Workflow
1. Click **Auto Guess Joints** in Upload Asset panel.
2. Backend returns scored guesses with `needs_user_confirmation`.
3. Review pending guesses in **Joint Settings** (Accept / Edit / Reject).
4. **Accept** appends the joint to the manifest and saves via `PUT /projects/{id}/manifest`.
5. **Reject** removes the guess from the pending list without saving.

## Playback
- Run artifacts populate `state_timeseries` in the store.
- **Timeline** tab and **Test Results** panel provide play/pause, scrubber, and frame summary.
- Viewport HUD toggles: Visual / Collision / Both, COM, Joints, Sensors, Wires.

## Persistence Checks
- Edit battery Z -> run `stand_balance` -> `max_pitch_deg` changes.
- Edit payload mass -> run `payload_carry` -> `min_torque_margin` changes.
- Edit actuator torque -> run `torque_margin` -> margin changes.
