# Agentic Simulation Layer — Codebase Audit

Audit date: June 2026. Purpose: map existing Buildables Genesis Workbench before adding the Agentic Simulation Layer (Part 1).

## Stack Summary

| Layer | Location | Technology |
|-------|----------|------------|
| Frontend | `apps/web` | Next.js 15 App Router, React 19, Tailwind, Three.js/R3F, Zustand |
| Backend | `apps/api` | FastAPI 0.115, uvicorn, Pydantic 2.x |
| Physics engine | Genesis (pip `genesis-world`) | Execution only — not intelligence layer |
| Data | `sim-data/` | File-based project storage (`SIM_DATA_ROOT` env override) |
| Dev | `scripts/dev-api.mjs`, `scripts/dev-web.mjs`, `npm run dev` | API :8000, web :3000 |

## Frontend Routes and Components

### Routes
- `/` → redirects to `/genesis`
- `/genesis` → `GenesisWorkbenchShell` (single-page workbench)

### Genesis Workbench (active)
| Component | Path | Role |
|-----------|------|------|
| `GenesisWorkbenchShell` | `apps/web/src/components/genesis-workbench/GenesisWorkbenchShell.tsx` | Top shell: Catalogue vs My Projects tabs |
| `GenesisCataloguePanel` | `.../GenesisCataloguePanel.tsx` | Showcase demo list |
| `GenesisDemoDetail` | `.../GenesisDemoDetail.tsx` | Launch catalogue demos |
| `GenesisProjectImport` | `.../GenesisProjectImport.tsx` | My Projects: upload, import, launch |
| `ImportValidationSummary` | `.../ImportValidationSummary.tsx` | Import validation display |
| `GenesisShowcaseViewport` | `.../GenesisShowcaseViewport.tsx` | 3D replay + telemetry viewer |
| `replay/*` | `.../replay/` | Replay canvas, controls, mesh loading |
| `telemetry/renderers/*` | `.../telemetry/renderers/` | Sensor-specific telemetry panels |

### API clients
- `apps/web/src/lib/api.ts` — core REST client
- `apps/web/src/lib/genesisWorkbenchApi.ts` — workbench readiness/launch
- `apps/web/src/lib/types.ts` — shared TypeScript types

### Legacy (unused by routes)
- `AppShell`, `WorkbenchLayout`, `ImportProjectModal`, `UploadAssetPanel` — manifest-editing UI superseded by Genesis workbench

## Backend Routes and Services

### Route modules (`apps/api/app/routes/`)
| Router | Key endpoints |
|--------|---------------|
| `health.py` | `GET /`, `GET /health` |
| `projects.py` | Import, upload, STEP pipeline, defaults, validation |
| `imports.py` | CAD import, URDF/MJCF generation, joint guessing |
| `assets.py` | Single-file asset upload (duplicate path with projects) |
| `manifests.py` | Manifest CRUD/validate |
| `genesis_showcase.py` | Catalogue launch, replay/timeseries/telemetry |
| `genesis_workbench.py` | Custom project readiness, `launch-web` |
| `genesis.py` | Native viewer, run-scene |
| `tests.py` | Manifest-based test catalog and execution |
| `scenarios.py`, `simulations.py` | Scenario/simulation runs |

### Upload and import flow
1. `POST /projects/import` — multipart files → `assets/imported/`
2. Detect URDF/MJCF → `parse_urdf` / `parse_mjcf`
3. `validate_urdf_meshes()` — resolve mesh paths, auto-map basenames
4. Write `import_validation.json` + update `manifest.buildables.physics.json`

**Services:**
- `app/services/importers/urdf_importer.py` — XML-based URDF parse
- `app/services/importers/mesh_validation.py` — mesh reference validation
- `app/services/importers/asset_resolver.py` — `package://`, `file://`, Windows path normalization
- `app/services/importers/import_validation.py` — human-readable validation messages
- `app/services/cad_import/step_mesh_converter.py` — FreeCAD STEP inspect/export

### Genesis launcher (execution engine)
| Path | Role |
|------|------|
| `genesis_showcase/example_script_runner.py` | `launch_showcase_demo()`, subprocess orchestration |
| `scripts/showcase_launcher.py` | Subprocess entry, headless + web recording |
| `genesis_workbench/custom_project_launcher.py` | Custom imported project web launch |
| `scripts/imported_robot_web_demo.py` | Custom project Genesis script |

### Catalogue metadata
- `genesis_showcase/showcase_script_catalog.py` — static `SHOWCASE_ENTRIES` (upstream Genesis examples)
- `genesis_catalog/test_catalog.py` — manifest-based test definitions
- `genesis_catalog/genesis_feature_catalog.py` — capability matrix

### Replay and telemetry recorders
| File | Output |
|------|--------|
| `scene_replay_exporter.py` | `state_timeseries.json` (rich replay bundle) |
| `replay_atomic_io.py` | Atomic writes, `replay_manifest.json` |
| `telemetry_recorder.py` | `telemetry_timeseries.json`, IMU channels |
| `sensor_capture.py` | Lidar, contact, depth, tactile frame payloads |

## Where Things Are Stored

### Project layout (`sim-data/projects/{project_id}/`)
```
manifest.buildables.physics.json
manifest_versions/{N}.json
assets/imported/          # uploaded URDF, STEP, meshes
assets/                   # legacy single-asset uploads
generated/collision/
generated/robot_description/
import_validation.json    # existing validation report
runs/run-{hex}/           # physics test runs
runs/showcase-{hex}/      # catalogue/custom web launches
```

### Global
- `sim-data/active_project.json` — active project pointer

### Replay JSON
- Showcase/custom: `runs/showcase-{hex}/state_timeseries.json`
- Physics tests: `runs/run-{hex}/state_timeseries.json`

### Telemetry JSON
- Embedded in replay bundle `telemetry` block
- Companion: `telemetry_timeseries.json`
- Test runs: `sensor_output.json`, `metrics.json`

## Python Dependencies (pre-agentic)
`apps/api/requirements.txt`:
- fastapi, uvicorn, pydantic, python-multipart
- genesis-world, trimesh, numpy

No pyproject.toml in apps/api. Optional runtime: PyTorch (via Genesis), FreeCAD CLI (STEP), gs-nyx-plugin.

## Hardcoded Assumptions to Remove

1. **`GenesisProjectImport.tsx`** — hardcoded `TEST_TYPES` dropdown (simulation/gui/imu/lidar/…) instead of data-driven test matrix
2. **`test_catalog.py`** — `supported_project_types: ["robot_dog", "robot_arm", …]` gates tests by manifest type, not uploaded assets
3. **`showcase_script_catalog.py`** — Franka Panda, Go2, Shadow Hand demo scripts as product brain
4. **`franka_asset_meshes.py`**, **`franka_visual_defs.py`** — Franka-specific replay mesh export
5. **`sensor_capture.py`** — `CONTACT_FOOT_ORDER = ("FR_foot", "FL_foot", …)` quadruped naming
6. **`demo_project_setup.py`** — default robot dog from `~/Downloads/robot_dog_buildables_demo.*`
7. **`import-from-downloads`** endpoint — hardcoded robot dog paths
8. **Manifest model** — `built_in_controller = "robot_dog_default"`
9. **`simulations.py`** — `robot_dog_controller` as default control path
10. **Duplicate upload route** — `projects.py` and `assets.py` both define `POST /projects/{id}/assets/upload`

## Gaps Addressed by Agentic Layer (Part 1)

- No typed preflight schemas for agent outputs
- No `asset_inventory.json` separate from manifest
- No data-driven test requirement matrix independent of `project_type`
- No deterministic planner before Genesis launch
- URDF inspection coupled to import flow, not callable as standalone preflight API
- STEP recovery tied to FreeCAD only; no structured optional CadQuery path
- Frontend shows validation but not full simulation plan with blocked/recommended tests
