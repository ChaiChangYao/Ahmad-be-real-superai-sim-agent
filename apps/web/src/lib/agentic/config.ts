import { getApiBase } from "../apiBase";

export const AGENTIC_API_BASE = getApiBase();

export const ENABLE_COPILOTKIT = process.env.NEXT_PUBLIC_ENABLE_COPILOTKIT === "true";
export const ENABLE_LLM_ASSISTANT = process.env.NEXT_PUBLIC_ENABLE_LLM_ASSISTANT === "true";
