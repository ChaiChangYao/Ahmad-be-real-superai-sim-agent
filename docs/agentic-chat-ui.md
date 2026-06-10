# Agentic Chat UI (Part 2)

## Chosen approach

**Custom Buildables Assistant** embedded in My Projects — not a full CopilotKit or Vercel chatbot clone.

| Tool | Decision |
|------|----------|
| CopilotKit | **Postponed** — action layer ready for future tool wiring |
| Vercel AI Chatbot | **Reference only** — chat layout and dropzone patterns adapted |

See [chat-ui-tooling-decision.md](./chat-ui-tooling-decision.md).

## Architecture

```
User → BuildablesAssistant (chat + dropzone)
     → lib/agentic/actions.ts (tool layer)
     → lib/agentic/api.ts → FastAPI agentic routes
     → planner / inspectors (source of truth)
```

## Chat message types

| Type | Renders |
|------|---------|
| `text` | Plain assistant/user prose |
| `user` | User bubble |
| `asset_summary` | Asset counts, links, joints |
| `missing_requirements` | MissingMeshTable + MissingMetadataTable |
| `test_recommendations` | TestRecommendationCards |
| `recovery_actions` | RecoveryActions buttons |
| `clarification_question` | Amber prompt |
| `simulation_plan` | Plan prose |
| `error` | Inline error + modal |

## Tool / action list (`lib/agentic/actions.ts`)

| Action ID | Function |
|-----------|----------|
| `inspect_uploaded_files` | scan + inspect |
| `recommend_tests` | plan + test requirements |
| `explain_missing_requirements` | per-test explanation |
| `generate_safe_defaults` | POST generate-defaults |
| `recover_from_step` | preview / missing meshes |
| `prepare_genesis_script` | stub (Part 3) |
| `run_simulation` | stub (Part 4) |
| `generate_engineering_report` | stub (Part 5) |
| `ask_buildables_cad` | CAD bridge stub |

## API endpoints used

| Endpoint | UI trigger |
|----------|------------|
| `POST /projects/{id}/scan` | upload, preflight |
| `POST /projects/{id}/inspect` | upload, preflight |
| `POST /projects/{id}/plan` | chat send, preflight |
| `POST /projects/{id}/parse-goal` | included in plan response |
| `GET /projects/{id}/test-requirements` | test cards |
| `GET/PUT /projects/{id}/agentic-state` | page refresh resume |
| `POST /projects/{id}/generate-defaults` | Use defaults button |
| `POST /projects/{id}/recover/*` | recovery actions |
| `POST /projects/{id}/cad-bridge/*` | Ask Buildables CAD |

## Deterministic vs LLM mode

| Mode | Flag | Behavior |
|------|------|----------|
| Deterministic (default) | `NEXT_PUBLIC_ENABLE_LLM_ASSISTANT=false` | `messages.ts` builds cards from `SimulationPlan` |
| LLM (future) | `NEXT_PUBLIC_ENABLE_LLM_ASSISTANT=true` | Summarize plan only; never override readiness |

## Environment variables

```
NEXT_PUBLIC_AGENTIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_ENABLE_COPILOTKIT=false
NEXT_PUBLIC_ENABLE_LLM_ASSISTANT=false
```

## Frontend files

| Path | Role |
|------|------|
| `lib/agentic/types.ts` | Typed schemas |
| `lib/agentic/api.ts` | API client |
| `lib/agentic/actions.ts` | Tool action layer |
| `lib/agentic/messages.ts` | Deterministic message builder |
| `lib/agentic/store.ts` | Zustand assistant state |
| `assistant/BuildablesAssistant.tsx` | Main shell |
| `assistant/*` | Cards, tables, modals |

## Backend additions (Part 2)

| Path | Role |
|------|------|
| `goal_parser.py` | User intent → test IDs |
| `project_state.py` | `agentic_project_state.json` |
| `safe_defaults.py` | Generate defaults per test |
| `buildables_cad_bridge.py` | Pillar 1 CAD stub |

## Future integration

1. CopilotKit tools → call `actions.ts` functions
2. LLM wrapper → rephrase `agent_explanation` only
3. Part 3 → enable `prepare_genesis_script` action
4. Part 4 → enable `run_simulation` or gate existing launch
