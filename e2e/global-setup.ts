const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const WEB = process.env.QA_WEB_BASE_URL ?? "http://127.0.0.1:3000";

async function waitForUrl(url: string, timeoutMs = 120_000): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
      if (res.ok) return;
    } catch {
      /* retry */
    }
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error(`Timed out waiting for ${url}`);
}

export default async function globalSetup() {
  await waitForUrl(`${API}/health`);
  await waitForUrl(`${WEB}/genesis`);
}
