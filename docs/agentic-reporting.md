# Agentic Engineering Reporting (Part 5)

## Architecture

Reporting is separate from execution:

```
Run artifacts → metrics_parser → run_analyzer → report_generator → report.json + report.md
```

Reporting **never** spawns Genesis. It reads completed/failed run directories only.

## Outputs

```
runs/{run_id}/report.json   # canonical typed report
runs/{run_id}/report.md      # human-readable export
```

## Deterministic-first

- Default path: Python metrics + rule-based templates → validated `EngineeringReport`
- Optional LLM polish: `ENABLE_LLM_REPORTER=true` (backend only)
- CrewAI: postponed — see `crewai-decision.md`

## Honesty policy (`limitations.py`)

- No stress/buckling/CFD/FEA numbers unless artifacts contain them
- Thermal demo fields labeled explicitly
- Skeleton fallback never claims full visual validation
- FEA/CFD readiness = checklist only

## API

| Method | Path |
|--------|------|
| POST | `/projects/{id}/runs/{run_id}/report` |
| POST | `/projects/{id}/runs/{run_id}/report/regenerate` |
| GET | `/projects/{id}/runs/{run_id}/report` |
| GET | `/projects/{id}/runs/{run_id}/report.md` |
| GET | `/projects/{id}/runs/{run_id}/summary` |

## Verification

```powershell
python apps/api/app/scripts/verify_reporting.py
```

## MVP loop

```
Upload → Inspect → Plan → Generate → Execute → Report
```
