export const AGENTIC_API_BASE =
  process.env.NEXT_PUBLIC_AGENTIC_API_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_BUILDABLES_API_URL ??
  "http://127.0.0.1:8000";

export const ENABLE_COPILOTKIT = process.env.NEXT_PUBLIC_ENABLE_COPILOTKIT === "true";
export const ENABLE_LLM_ASSISTANT = process.env.NEXT_PUBLIC_ENABLE_LLM_ASSISTANT === "true";
