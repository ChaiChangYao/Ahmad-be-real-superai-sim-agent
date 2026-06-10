const FALLBACK_ADJECTIVES = [
  "Skibidi",
  "Rizzler",
  "Sigma",
  "Gyatt",
  "Delulu",
  "Ohio",
  "Fanum",
  "Mewing",
  "Bussin",
  "No-Cap",
];

const FALLBACK_NOUNS = [
  "Mech",
  "Doggo",
  "Bot",
  "Unit",
  "Chassis",
  "Walker",
  "Droid",
  "Golem",
];

export function localBrainrotProjectName(): string {
  const adj = FALLBACK_ADJECTIVES[Math.floor(Math.random() * FALLBACK_ADJECTIVES.length)];
  const noun = FALLBACK_NOUNS[Math.floor(Math.random() * FALLBACK_NOUNS.length)];
  const suffix = Math.floor(Math.random() * 900) + 100;
  return `${adj} ${noun} ${suffix}`;
}

export function sanitizeProjectName(raw: string): string {
  const cleaned = raw
    .replace(/^["'`]+|["'`]+$/g, "")
    .replace(/^project name:\s*/i, "")
    .replace(/\s+/g, " ")
    .trim();
  return cleaned.slice(0, 64);
}

/** Fetches a Gen Z brainrot project name from the Vercel AI Gateway route (server-side key). */
export async function fetchBrainrotProjectName(): Promise<string> {
  try {
    const res = await fetch("/api/ai/project-name", { cache: "no-store" });
    if (!res.ok) return localBrainrotProjectName();
    const data = (await res.json()) as { name?: string };
    const name = data.name ? sanitizeProjectName(data.name) : "";
    return name || localBrainrotProjectName();
  } catch {
    return localBrainrotProjectName();
  }
}
