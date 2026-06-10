# Agentic Execution (Part 4)

## Architecture

Genesis remains the physics engine. Buildables owns execution orchestration:

```
POST /runs → execution.runner → local_runner (default)
  → showcase_launcher.py --headless --record-web
  → runs/agentic-{id}/
```

Backends: `local` (default), `docker` (stub), `e2b` (stub). Select via `BUILDABLES_EXECUTION_BACKEND`.

## Run directory layout

```
sim-data/projects/{project_id}/runs/{run_id}/
  run.json
  manifest.json
  stdout.log
  stderr.log
  combined.log
  state_timeseries.json
  telemetry_timeseries.json
  replay_manifest.json   # when showcase recorder active
  generated/
    script.py
    script.context.json
  artifacts/
```

## Manifest gating

Frontend loads replay only when `manifest.json` has `status: "complete"` and `visual.hasReplay`. Telemetry loads only when `telemetry.hasTelemetry`.

## Security

- Only scripts from `generated/scripts/{script_id}.py`
- Re-validated with AST safety before spawn
- Outputs confined to run directory
- Timeout + cancel supported
- Logs redact API keys/tokens

## API endpoints

| Method | Path |
|--------|------|
| POST | `/projects/{id}/runs` |
| GET | `/projects/{id}/runs` |
| GET | `/projects/{id}/runs/{run_id}` |
| POST | `/projects/{id}/runs/{run_id}/cancel` |
| GET | `/projects/{id}/runs/{run_id}/logs` |
| GET | `/projects/{id}/runs/{run_id}/events` (SSE) |
| GET | `/projects/{id}/runs/{run_id}/manifest` |
| GET | `/projects/{id}/runs/{run_id}/replay` |
| GET | `/projects/{id}/runs/{run_id}/telemetry` |

## Web mode env

- `BUILDABLES_WEB_MODE=1`
- `MPLBACKEND=Agg`
- `BUILDABLES_SKIP_MANUAL_REPLAY_WRITE=1`
- `CREATE_NO_WINDOW` on Windows

## Verification

```powershell
python apps/api/app/scripts/verify_execution.py
```
