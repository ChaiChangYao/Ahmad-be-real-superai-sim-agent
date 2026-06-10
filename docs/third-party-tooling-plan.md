# Third-Party Tooling Plan

Decisions for external repos/libraries in the Agentic Simulation Layer. Rule: prefer package manager installs; clone reference repos only into `external/references/` for inspection (gitignored).

## Summary Table

| Repo / Library | Decision | Install method | Part 1 usage |
|----------------|----------|----------------|--------------|
| [pydantic-ai](https://github.com/pydantic/pydantic-ai) | **use as dependency** | `pip install pydantic-ai` | Typed agent framework; deterministic planner first, LLM wrapper in Part 2 |
| [urdfpy](https://github.com/mmatl/urdfpy) | **use as dependency** | `pip install urdfpy` | URDF structure parsing in `urdf_inspector.py` |
| [trimesh](https://github.com/mikedh/trimesh) | **use as dependency** | Already in requirements | Mesh validation in `mesh_inspector.py` |
| [CadQuery](https://github.com/CadQuery/cadquery) | **optional dependency** | `pip install cadquery` (heavy OCC) | STEP recovery stub; guarded by `CADQUERY_AVAILABLE` |
| [lxml](https://github.com/lxml/lxml) | **use as dependency** | `pip install lxml` | Robust XML parsing fallback for URDF/MJCF |
| [CopilotKit](https://github.com/CopilotKit/CopilotKit) | **postpone** | npm (Part 2) | Chat/workbench UI |
| [vercel/chatbot](https://github.com/vercel/chatbot) | **postpone** | npm (Part 2) | Alternative chat UI template |
| [CrewAI](https://github.com/crewAIInc/crewAI) | **postpone** | `pip install crewai` optional | Multi-agent only if pydantic-ai single-flow too limited |
| [E2B](https://github.com/e2b-dev/E2B) | **postpone** | `pip install e2b` optional | Remote sandbox; local Genesis worker first |
| FreeCAD CLI | **existing** | System install, on PATH | Current STEP pipeline (`step_mesh_converter.py`) |

## Per-repo rationale

### pydantic-ai — use as dependency
Primary typed agent framework. Part 1 uses Pydantic schemas and deterministic planning; Part 2 adds LLM explanation layer via pydantic-ai agents without dict soup.

### urdfpy — use as dependency
Standard URDF parsing for links, joints, limits, inertial data. Combined with direct XML walk for mesh path validation (urdfpy alone may not expose all mesh refs robustly).

### trimesh — use as dependency
Already installed. STL/OBJ/GLB/PLY load, watertight check, bounds, volume, center of mass.

### CadQuery — optional dependency
STEP/OpenCASCADE install is heavy on Windows. Part 1 exposes stubs that return `missing_optional_dependency` when absent. FreeCAD remains primary STEP path.

### CopilotKit / vercel/chatbot — postpone to Part 2
Chat UI not in Part 1 scope. Reference patterns may be cloned to `external/references/` for inspection only.

### CrewAI — postpone
Build deterministic typed workflows first. Add only if multi-agent orchestration exceeds pydantic-ai capabilities.

### E2B — postpone
Local Genesis subprocess worker is MVP. E2B for optional cloud sandbox in later stage.

## Reference clone policy

```
external/references/     # gitignored
  copilotkit/              # template/reference only — never import in production
  vercel-chatbot/
```

Production code must never `import` from `external/references/`.

## Feature flags (`dependencies.py`)

| Flag | When true |
|------|-----------|
| `CADQUERY_AVAILABLE` | `import cadquery` succeeds |
| `E2B_AVAILABLE` | `import e2b` succeeds |
| `CREWAI_AVAILABLE` | `import crewai` succeeds |

Missing optional deps return structured API message: *"Feature not available: install cadquery to enable STEP mesh recovery."*

## Windows install notes

- Required deps (pydantic-ai, urdfpy, lxml, trimesh) install via pip without system dependencies
- CadQuery requires OpenCASCADE — keep optional, document in readiness endpoint
- FreeCAD CLI: separate system install for existing STEP pipeline
- E2B/CrewAI: optional, no Part 1 requirement
