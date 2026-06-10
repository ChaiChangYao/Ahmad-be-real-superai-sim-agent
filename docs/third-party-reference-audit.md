# Third-party reference audit

Cloned repos live under `external/references/` (gitignored). Used for inspection only — production depends on npm/pip packages.

Run: `npm run refs:clone`

## copilotkit

| Field | Value |
|-------|-------|
| Path | `external/references/copilotkit` |
| Why | Part 2 browser assistant / future tool wiring |
| Useful | React copilot UI patterns, tool action cards |
| Usage | Reference only — CopilotKit postponed |
| License | MIT |
| Adapted | None in production |

## vercel-ai-chatbot

| Field | Value |
|-------|-------|
| Path | `external/references/vercel-ai-chatbot` |
| Why | Chat UI layout reference |
| Useful | Message list, composer, streaming patterns |
| Usage | Reference only |
| License | Check repo LICENSE |
| Adapted | Pill composer, attachment preview row, submit-on-enter |

### Part 2 UI refresh (pill entry)

Inspected `components/chat/multimodal-input.tsx`, `preview-attachment.tsx`, `ai-elements/prompt-input`:

| Vercel pattern | Buildables adaptation |
|----------------|----------------------|
| `attachments` state above textarea | `AttachmentTray` chips inside rounded pill |
| Paperclip / file picker | `+` button left in `PillComposer` |
| `PromptInputSubmit` arrow | Orange `↑` submit right |
| Submit sends message + files together | `handleEntrySubmit` → `uploadAndPreflight` on Enter/↑ only |
| Rounded `input-group` shell | `rounded-[28px]` pill on `ProjectEntryScreen` |

CopilotKit tool cards remain reference-only; structured cards use `TestRecommendationCards`, `SimulationPlanCard`, `RecoveryActions`.

## urdfpy

| Field | Value |
|-------|-------|
| Path | `external/references/urdfpy` |
| Why | URDF loading, joint/link traversal |
| Useful | `URDF.load`, link/joint graph, mesh filename refs |
| Usage | Optional pip dependency + XML fallback in `urdf_inspector.py` |
| License | MIT |
| Adapted | Inspection patterns, not vendored parser |

## trimesh

| Field | Value |
|-------|-------|
| Path | `external/references/trimesh` |
| Why | Mesh validation, watertight checks |
| Useful | `trimesh.load`, bounds, `is_watertight` |
| Usage | pip dependency via `mesh_inspector.py` |
| License | MIT |
| Adapted | Watertight/bounds inspection |

## cadquery

| Field | Value |
|-------|-------|
| Path | `external/references/cadquery` |
| Why | STEP → mesh recovery |
| Useful | STEP import examples, STL export |
| Usage | Optional — FreeCAD preferred on Windows |
| License | Apache 2.0 |
| Adapted | Stub recovery in `cad_recovery.py` |

## pydantic-ai

| Field | Value |
|-------|-------|
| Path | `external/references/pydantic-ai` |
| Why | Typed agent tool outputs |
| Useful | Structured tool results, schema validation |
| Usage | Postponed — Part 1–3 use Pydantic models directly |
| License | MIT |
| Adapted | Schema style in `codegen/schemas.py` |

## crewai

| Field | Value |
|-------|-------|
| Path | `external/references/crewai` |
| Why | Multi-agent orchestration option |
| Usage | Postponed (Stage 8) |
| License | MIT |

## e2b

| Field | Value |
|-------|-------|
| Path | `external/references/e2b` |
| Why | Sandboxed script execution |
| Usage | Postponed (Stage 7) |
| License | Check repo LICENSE |

## genesis-world

| Field | Value |
|-------|-------|
| Path | `external/references/genesis-world` |
| Why | Genesis scene/sensor API patterns for templates |
| Useful | `examples/rigid/`, `examples/sensors/`, `examples/tutorials/`, headless scene setup |
| Usage | Reference only — runtime uses pip `genesis-world` |
| License | Check Genesis repo LICENSE |
| Adapted | Web-mode scene bootstrap in `runtime/scene_helpers.py` |

---

## Part 3 additions

### Genesis examples used as template references

- Rigid scene + plane + URDF load → `gravity_stability`, `joint_sweep`
- Headless `show_viewer=False` → all templates
- Sensor examples → `imu_sensor`, `contact_force`, `depth_camera`
- No native viewer / matplotlib → `safe_plotting.py`

### URDF / trimesh / CadQuery APIs used

- **urdfpy**: optional parse in inspector; skeleton URDF via `generate_urdf`
- **trimesh**: mesh bounds/watertight in preflight
- **cadquery**: postponed; STEP preview via FreeCAD path

### Pydantic AI patterns

- **Used**: Pydantic v2 models for `CodeGenResult`, `GenesisScriptContext`, validation
- **Postponed**: pydantic-ai agent runner — deterministic codegen first

---

## Part 4 additions

### E2B patterns inspected

- SDK sandbox lifecycle, file upload, command execution
- **Usage**: Stub only — `e2b_runner.py` checks `E2B_AVAILABLE` + `E2B_API_KEY`
- **Postponed**: Full Genesis execution in E2B (GPU/graphics unverified)

### Genesis execution / headless patterns

- `showcase_launcher.py --headless --record-web`
- `BUILDABLES_RECORD_PATH`, `MPLBACKEND=Agg`, `show_viewer=False`
- **Adapted**: `execution/local_runner.py` spawns launcher with web env

### Streaming UI patterns (vercel-ai-chatbot, copilotkit)

- Log tail polling, status cards, failure modals
- **Adapted**: `RunExecutionCard`, `pollAgenticRun`, SSE `/events` endpoint
- **Postponed**: CopilotKit live tool streaming

### What was adapted

- Subprocess argv array (Windows path-safe)
- Log tailer + combined.log
- Manifest gating for replay/telemetry
- `parse_run_failure` log patterns from showcase runner

---

## Part 5 additions

### pydantic-ai patterns

- Structured tool outputs, schema validation
- **Usage**: Optional `pydantic_reporter.py` behind `ENABLE_LLM_REPORTER=false`
- **Postponed**: Full pydantic-ai agent for reporting

### CrewAI patterns

- Multi-agent crew/task orchestration
- **Usage**: Reference only — see `docs/crewai-decision.md`
- **Postponed**: No runtime dependency in MVP

### trimesh / replay_motion_diagnostics

- Mesh watertight/bounds in `parse_mesh_metrics`
- `analyze_replay_motion()` for motion heuristics
- **Adapted**: `metrics_parser.py`, `run_analyzer.py`

### CopilotKit / vercel-ai-chatbot

- Report cards, action buttons, chat closing messages
- **Adapted**: `EngineeringReportCard`, `engineering_report` message type
