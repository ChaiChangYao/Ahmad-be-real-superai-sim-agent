import { NextResponse } from "next/server";

import { localBrainrotProjectName, sanitizeProjectName } from "@/lib/ai/brainrotProjectName";

const GATEWAY_URL = "https://ai-gateway.vercel.sh/v1/chat/completions";
const MODEL = "openai/gpt-oss-120b";

export async function GET() {
  const apiKey = process.env.AI_GATEWAY_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ name: localBrainrotProjectName(), source: "fallback" });
  }

  try {
    const res = await fetch(GATEWAY_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          {
            role: "system",
            content:
              "Reply with ONLY one short robot project name (2-6 words). Gen Z brainrot vibe: skibidi, rizz, sigma, gyatt, fanum tax, no cap, delulu, mewing, ohio, aura, mogging. Be random and absurd. No quotes, no punctuation at the end, no explanation.",
          },
          {
            role: "user",
            content: `Seed ${Date.now()}-${Math.random()}: invent a brand-new project name.`,
          },
        ],
        max_tokens: 32,
        temperature: 1.15,
      }),
    });

    if (!res.ok) {
      return NextResponse.json({ name: localBrainrotProjectName(), source: "fallback" });
    }

    const data = (await res.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    const raw = data.choices?.[0]?.message?.content ?? "";
    const name = sanitizeProjectName(raw) || localBrainrotProjectName();
    return NextResponse.json({ name, source: "ai" });
  } catch {
    return NextResponse.json({ name: localBrainrotProjectName(), source: "fallback" });
  }
}
