/** Shared API base URL for browser requests (local dev vs Vercel production proxy). */
export function getApiBase(): string {
  const explicit =
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    process.env.NEXT_PUBLIC_AGENTIC_API_URL ??
    process.env.NEXT_PUBLIC_BUILDABLES_API_URL;
  if (explicit) {
    return explicit.replace(/\/$/, "");
  }
  if (process.env.NODE_ENV === "production") {
    return "/backend";
  }
  return "http://127.0.0.1:8000";
}

export const API_PRODUCTION_HINT =
  "Deploy the Python API on Render (see render.yaml). Set NEXT_PUBLIC_API_BASE_URL or API_UPSTREAM_URL on Vercel, then redeploy. Genesis sims need Render Starter+ RAM; free tier may OOM during physics runs.";
