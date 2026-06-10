# Agentic Simulation Roadmap

## Stage 1 — Preflight intelligence layer (Part 1) ✅

- Typed Pydantic schemas for all agent outputs
- File inventory scanner (`asset_inventory.json`)
- URDF/MJCF inspector with mesh path validation
- Mesh inspector (trimesh)
- Data-driven test requirement matrix (8 MVP tests)
- Deterministic planner (no hallucinated runnable tests)
- CAD recovery stubs (FreeCAD delegation)
- Preflight API endpoints
- Agentic Preflight panel in My Projects
- Documentation: audit, tooling plan, architecture

## Stage 2 — Browser assistant (Part 2) ✅

- Buildables Assistant chat panel in My Projects
- Upload-driven scan → inspect → plan workflow
- Typed message cards (tests, missing meshes, recovery actions)
- Frontend action/tool layer (`lib/agentic/actions.ts`)
- Goal parser, project state persistence, safe defaults API
- Buildables CAD bridge stub
- Deterministic mode (no LLM key required)
- CopilotKit postponed; Vercel chatbot reference only

### Remaining for Stage 2+

- Optional CopilotKit tool wiring
- pydantic-ai LLM summarization (presentation only)

## Stage 3 — Code generation from Genesis templates (Part 3) ✅

- Code-Gen Agent (`apps/api/app/services/agentic/codegen/`)
- Template registry + Jinja2 templates (`templates/*.py.j2`)
- Runtime helper library (`runtime/`)
- AST script safety validation
- API: `generate-script`, `generated-scripts` CRUD
- UI: test config panel + generated code viewer
- Docs: `agentic-codegen.md`, `third-party-reference-audit.md` Part 3 section
- Verification: `apps/api/app/scripts/verify_codegen.py`

## Stage 4 — Local Genesis execution validation (Part 4) ✅

- Execution package (`apps/api/app/services/agentic/execution/`)
- Local worker via `showcase_launcher.py --headless --record-web`
- Run lifecycle API: start, poll, cancel, logs, manifest, replay, telemetry
- Docker/E2B stubs with structured unavailable errors
- Frontend: Run Simulation, manifest-gated replay, failure modal
- Docs: `agentic-execution.md`, `deployment-architecture.md`
- Verification: `verify_execution.py`

## Stage 5 — Engineering reporter (Part 5) ✅

- Reporting package (`apps/api/app/services/agentic/reporting/`)
- Deterministic metrics parser (manifest, replay, telemetry, logs, project context)
- Run analyzer + recommendations + limitations honesty policy
- `report.json` + `report.md` per run; API POST/GET report + summary
- Frontend: EngineeringReportCard/Panel/Modal, auto-generate after run
- Docs: `agentic-reporting.md`, `crewai-decision.md`
- Verification: `verify_reporting.py`

## MVP complete ✅

Core loop:

```
Upload → Inspect → Plan → Generate → Execute → Report
```

## Stage 6 — Post-MVP polish (optional)

- Vercel/API deployment hardening
- End-to-end regression suite
- Catalogue cleanup / demo migration
- Golden-path demo scripts and seed projects
- Eval cases for hackathon reliability

## Stage 7 — Optional E2B / Docker sandbox

- Remote execution for untrusted generated scripts
- Guarded by `E2B_AVAILABLE` feature flag
- Local worker remains default

## Stage 8 — Optional CrewAI multi-agent orchestration

- Only if pydantic-ai single-flow becomes too limited
- Critic / Code-Gen / Reporter as separate agents
- Guarded by `CREWAI_AVAILABLE`

## Stage 9 — FEA / CFD readiness expansion

- Expand readiness checks with domain-specific validators
- Do not claim full FEA/CFD solver in Genesis unless implemented
- Material, BC, load capture via chat/workbench forms
