# Agentic Simulation Layer — Part 1 Verification Results

## Commands to run

```powershell
cd "c:\Users\user\Physics Sim Buildables\PhysicsSimBuildables"

# Install dependencies
pip install -r apps/api/requirements.txt

# Run verification script
cd apps/api
python app/scripts/verify_agentic_layer.py

# Start dev stack
npm run dev
```

## API smoke tests

```powershell
curl http://127.0.0.1:8000/agentic/dependencies
curl -X POST http://127.0.0.1:8000/projects/imported-85653eba/scan
curl -X POST http://127.0.0.1:8000/projects/imported-85653eba/inspect
curl -X POST http://127.0.0.1:8000/projects/imported-85653eba/plan -H "Content-Type: application/json" -d "{\"user_goal\": \"joint sweep IMU\"}"
curl http://127.0.0.1:8000/projects/imported-85653eba/test-requirements
```

## Test cases

| Case | Input | Expected | Result |
|------|-------|----------|--------|
| 1 | URDF + STEP, missing STLs | 82 missing meshes, recovery tasks, FEA/CFD blocked | PASS — `missing_meshes=82`, `generation_tasks` includes `recover_missing_meshes_from_step` |
| 2 | URDF + full mesh zip (`imported-85653eba`) | `missing_mesh_count=0`, gravity + joint_sweep recommended | PASS — `missing=0`, 6 tests recommended |
| 3 | STEP only | Robot tests blocked, rigid preview path | PASS — `joint_sweep` blocked; `gravity_stability` runnable when STEP present |
| 4 | IMU on robot without sensor metadata | IMU with default attach link question | PASS — `imu can_run=True`, question for `base_link` |
| 5 | CFD goal | Blocked, explains missing BCs | PASS — `can_run=False`, blockers mention fluid domain |

## Files created

### Backend (`apps/api/app/services/agentic/`)
- `__init__.py`, `dependencies.py`, `schemas.py`, `errors.py`
- `file_inventory.py`, `urdf_inspector.py`, `mesh_inspector.py`
- `test_requirements.py`, `planner.py`
- `cad_recovery.py`, `codegen.py`, `executor.py`, `reporter.py`

### Routes
- `apps/api/app/routes/agentic.py` (registered in `main.py`)

### Frontend
- `apps/web/src/lib/agenticApi.ts`
- `apps/web/src/components/genesis-workbench/AgenticPreflightPanel.tsx`
- Integration in `GenesisProjectImport.tsx`

### Docs
- `docs/agentic-simulation-audit.md`
- `docs/third-party-tooling-plan.md`
- `docs/agentic-simulation-architecture.md`
- `docs/agentic-simulation-roadmap.md`
- `docs/agentic-verification-results.md`

### Scripts
- `apps/api/app/scripts/verify_agentic_layer.py`

## Dependencies added

```
pydantic-ai>=0.0.14
urdfpy>=0.0.22
lxml>=5.0.0
```

Optional (commented): cadquery, e2b, crewai

**Note:** `urdfpy` pins `networkx==2.2` which may fail on Python 3.11+. The inspector falls back to XML parsing via `urdf_importer` when urdfpy is unavailable.

## API endpoints

| Method | Path |
|--------|------|
| GET | `/agentic/dependencies` |
| POST | `/projects/{id}/scan` |
| POST | `/projects/{id}/inspect` |
| POST | `/projects/{id}/plan` |
| GET | `/projects/{id}/test-requirements` |
| POST | `/projects/{id}/recover/step-preview` |
| POST | `/projects/{id}/recover/missing-meshes` |
| GET | `/projects/{id}/recover/status` |

## Schema summary

10 core Pydantic models: `UploadedAsset`, `RobotDescriptionInspection`, `MeshReference`, `MeshInspection`, `SimulationTestSpec`, `TestReadinessResult`, `SimulationPlan`, `GeneratedSimulationScript`, `ExecutionResult`, `EngineeringReport` (+ `RecoveryResult`, `ProjectInspectionReport`).

## Test matrix summary

8 MVP tests: `gravity_stability`, `joint_sweep`, `imu_sensor`, `contact_force`, `depth_camera`, `thermal_grid_readiness`, `fea_readiness`, `cfd_readiness`.
