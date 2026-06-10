# Genesis vs Web Viewer

## Source of Truth

- Genesis backend stepping is authoritative.
- Web frontend replay is a consumer of Genesis artifacts (`state_timeseries`, render artifacts, logs, metrics).

## Native Viewer

- Endpoint: `POST /projects/{project_id}/genesis/native-viewer/run`
- Purpose: local debugging with `show_viewer=True`.

## Web Replay

- Endpoint: `POST /projects/{project_id}/genesis/run-scene`
- Uses `show_viewer=False`.
- Stores state and metrics for browser replay.

## Important Rule

Frontend-only animation is never treated as proof of physics correctness.
