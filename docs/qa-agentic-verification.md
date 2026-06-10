# Agentic QA Verification

Single entry point for validating the Buildables Agentic Simulation Layer end-to-end.

## Run the suite

```powershell
cd "c:\Users\user\Physics Sim Buildables\PhysicsSimBuildables"

# Backend + API E2E + web build (no browser)
npm run qa:agentic

# Full suite including Playwright browser E2E (starts API + web)
npm run qa:agentic:e2e
```

## What `npm run qa:agentic` runs

| Step | Script | Required | What it proves |
|------|--------|----------|----------------|
| Setup | `npm run setup:api` | Yes | API venv, uvicorn, Genesis import |
| Part 1 | `verify_agentic_layer.py` | Yes | Scan, inspect, plan, missing mesh detection, blocked tests |
| Part 3 | `verify_codegen.py` | Yes | Template codegen, safety, no Franka hardcoding |
| Part 4 | `verify_execution.py` | No* | Run dirs, unsafe script block, Docker stub |
| Part 5 | `verify_reporting.py` | Yes | Engineering reports from run artifacts |
| API E2E | `verify_agentic_api_e2e.py` | Yes | HTTP import → preflight → codegen → run → report → upload |
| Web | `npm run build:web` | Yes | TypeScript compiles |

\*Execution step is optional when Genesis is unavailable; failures are warned, not fatal.

With `--e2e` / `QA_E2E=1`:

| Step | Script | What it proves |
|------|--------|----------------|
| Playwright | `e2e/agentic-*.spec.ts` (14 tests) | Full browser golden path: upload, preflight, codegen, run, report panel, replay viewer, telemetry layout |

Playwright specs:
- `agentic-workbench.spec.ts` — health, entry screen, upload preflight
- `agentic-upload-preflight.spec.ts` — attachment tray, missing mesh table, blocked tests
- `agentic-generate-run.spec.ts` — script viewer, run card, failure modal / copy logs
- `agentic-report-layout.spec.ts` — non-sensor telemetry hidden; IMU telemetry (skip if no samples); API report
- `agentic-replay-report.spec.ts` — browser engineering report panel; replay controls (skip if no frames)

## Existing scripts (reference)

### `verify_agentic_layer.py`
- **Tests:** dependency flags, test matrix, URDF+missing meshes, full mesh project, STEP-only, IMU/CFD readiness
- **Does not test:** HTTP layer, browser UI, codegen, execution, reports

### `verify_codegen.py`
- **Tests:** 10 codegen cases (skeleton, sensors, blocked FEA/STEP-only, no hardcoded robots)
- **Does not test:** HTTP endpoints, Genesis runtime execution

### `verify_execution.py`
- **Tests:** Run directory layout, unsafe script rejection, Docker unavailable, two-run isolation
- **Does not test:** Browser replay, SSE log streaming UI

### `verify_reporting.py`
- **Tests:** Report generator with fixture runs (missing mesh, IMU, thermal demo, FEA/CFD readiness)
- **Does not test:** UI report card rendering

### `verify_agentic_api_e2e.py`
- **Tests:** Full HTTP flow via FastAPI TestClient
- **Does not test:** Browser DOM, Three.js replay viewer

### `api_smoke_test.py` / `smoke:genesis`
- **Tests:** Catalogue scenario metrics (legacy workbench)
- **Does not test:** Agentic assistant flow

### `npm run test:web`
- **Tests:** Only `next build` — **not** UX regression

## Browser E2E

- **Framework:** Playwright (`e2e/playwright.config.ts`)
- **Specs:** `e2e/agentic-workbench.spec.ts`
- **Selectors:** `data-testid` on `ProjectEntryScreen`, `PillComposer`, `BuildablesAssistant`

### Playwright skip conditions (honest)
- Replay viewer test skips when run produces zero frames (Genesis product limit on gravity fixture)
- IMU telemetry test skips when run produces zero telemetry samples
- Failure modal + copy logs verified when modal appears (`agentic-generate-run.spec.ts`)

## Gaps and honest claims

| Claim | Proven by |
|-------|-----------|
| Upload works (API) | `verify_agentic_api_e2e.py`, Playwright API test |
| Upload works (browser) | Playwright pill composer test |
| Preflight recommends/blocks tests | `verify_agentic_layer.py`, API E2E plan step |
| Genesis script generated | `verify_codegen.py`, API E2E `generate-script` |
| Run manifest/logs exist | `verify_execution.py`, API E2E run step (when Genesis installed) |
| Report created | `verify_reporting.py`, API E2E report step |
| Replay in browser | **Not automated yet** — manual or future Playwright extension |
| Telemetry UI for sensors | **Not automated yet** |

## Environment notes

- Genesis-heavy steps skip with clear reason when `genesis` is not importable.
- Windows paths with spaces are exercised by local runner and API E2E.
- Playwright E2E expects API on `:8000` and web on `:3000` (started by `qa:agentic:e2e`).

## First-time Playwright setup

```powershell
npx playwright install chromium
```

## Last verified (local)

| Command | Result |
|---------|--------|
| `npm run qa:agentic` | PASS (all 7 steps) |
| `npx playwright test --config e2e/playwright.config.ts` | PASS (4/4 browser + API upload tests) |

**Known limitations on this machine:**
- Genesis **execution runs** often end `failed` (exit 1) for `gravity_stability` — run dirs, logs, and reports still validate; full replay completion is not asserted in QA yet.
- Optional deps (`pydantic-ai`, `cadquery`, `e2b`, `crewai`) reported as missing — expected for MVP.
