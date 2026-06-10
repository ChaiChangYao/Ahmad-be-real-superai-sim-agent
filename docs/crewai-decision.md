# CrewAI Decision

## Status: Postponed

CrewAI multi-agent orchestration is **not** used in the Buildables MVP.

## Why postponed

1. **Deterministic MVP** — Parts 1–5 use typed Pydantic pipelines (preflight, codegen, execution, reporting) without multi-agent coordination overhead.
2. **Debuggability** — Engineering reports must cite artifact paths and metrics, not opaque agent chains.
3. **Dependency weight** — CrewAI adds runtime and API surface not required for hackathon reliability.

## What we use instead

| Need | Solution |
|------|----------|
| Structured outputs | Pydantic v2 models |
| Optional LLM polish | `pydantic_reporter.py` behind `ENABLE_LLM_REPORTER=false` |
| Tool actions | `lib/agentic/actions.ts` + assistant action cards |
| Future multi-step flows | CopilotKit or pydantic-ai (evaluated in reference audit) |

## Extensibility

If multi-agent workflows are needed later:

- **Inspector agent** → already `inspect` + `plan` APIs
- **Codegen agent** → `codegen/generator.py`
- **Reporter agent** → `reporting/report_generator.py`

CrewAI could wrap these as tools without rewriting core logic.

## Reference

Cloned repo: `external/references/crewai` (inspection only, not a runtime dependency).
