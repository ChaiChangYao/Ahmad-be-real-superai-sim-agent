# Chat UI Tooling Decision

## Current frontend stack

| Item | Value |
|------|-------|
| Framework | **Next.js 15** App Router |
| UI | React 19, TypeScript, Tailwind CSS |
| 3D | Three.js + `@react-three/fiber` |
| Layout | `react-resizable-panels` |
| State | React `useState` + Zustand (legacy workbench) |
| Package manager | **npm** (root workspaces: `apps/web`, `packages/schemas`) |
| Routes | `/` → `/genesis` (single workbench page) |
| My Projects | Tab in `GenesisWorkbenchShell` — pill entry screen → workbench split (assistant left / viewer right) |
| Upload | Staged on pill entry (`PillComposer` + `AttachmentTray`); upload on submit via `uploadAndPreflight` |
| Agentic API | Part 1 `lib/agenticApi.ts` → Part 2 `lib/agentic/api.ts` |

## Reference repos evaluated

### CopilotKit (`CopilotKit/CopilotKit`)

**Useful for:** embedded copilot, frontend state sync, tool/action calls, generative UI cards.

**Decision: POSTPONED for Part 2**

- Adds significant dependency surface for a hackathon demo.
- Part 2 action layer (`lib/agentic/actions.ts`) is designed with the same interface CopilotKit tools would call later.
- Feature flag `NEXT_PUBLIC_ENABLE_COPILOTKIT=false` by default.
- Patterns documented in `docs/agentic-chat-ui.md` for Part 3 wiring.

### Vercel AI Chatbot (`vercel/ai-chatbot`)

**Useful for:** Next.js chat layout, streaming messages, file-upload UX patterns.

**Decision: REFERENCE ONLY (not installed)**

- App already has Next.js workbench layout — copying the whole chatbot app would rewrite the frontend.
- Adapted patterns: pill composer (`+` attach, `↑` submit), attachment chips above textarea (no auto-upload), message list scroll, structured message cards, orange `#FF6A1A` accent.
- No production imports from `external/references/vercel-ai-chatbot`.

## Final chosen approach

**Custom Buildables Assistant** integrated into My Projects:

1. **Deterministic mode (default)** — user types goal → `parse-goal` + `plan` APIs → structured chat cards. No LLM key required.
2. **Optional LLM mode** — behind `NEXT_PUBLIC_ENABLE_LLM_ASSISTANT` (future: summarize plan via API).
3. **Action layer** — `actions.ts` shared by chat buttons and future CopilotKit tools.
4. **Typed messages** — text, asset_summary, test_recommendations, missing_requirements, etc.
5. **Layout** — two-phase My Projects: centered `ProjectEntryScreen` (pill only) → workbench vertical split (assistant chat, optional collapsed legacy viewer controls).

## Why not CopilotKit now

- Preflight intelligence is deterministic; LLM is presentation layer only.
- Demo must work with zero API keys.
- CopilotKit integration is a thin wrapper in Part 3 once actions are stable.

## Patterns copied/adapted (not vendored)

| Pattern | Source inspiration | Buildables implementation |
|---------|-------------------|---------------------------|
| Pill composer + attach row | Vercel `multimodal-input.tsx` | `PillComposer.tsx`, `AttachmentTray.tsx`, `ProjectEntryScreen.tsx` |
| Chat message list | Vercel chatbot | `BuildablesAssistant.tsx`, `AssistantMessageView.tsx` |
| File dropzone (optional) | Vercel chatbot | `UploadDropzone.tsx` (hidden in workbench; entry uses pill attach) |
| Tool/action registry | CopilotKit concept | `lib/agentic/actions.ts` |
| Structured cards | CopilotKit generative UI | `TestRecommendationCards.tsx`, `MissingMeshTable.tsx` |
