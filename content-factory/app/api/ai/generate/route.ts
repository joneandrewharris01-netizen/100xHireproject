import { NextResponse } from "next/server";
import { readConfig, getApiKey } from "../../../../lib/config";
import { getProvider } from "../../../../lib/ai/provider";
import type { ContentMode } from "../../../../src/types/content";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { prompt, mode, tone, hooks } = body as {
      prompt: string;
      mode: ContentMode;
      tone?: string;
      hooks?: number;
    };

    if (!prompt || !mode) {
      return NextResponse.json(
        { error: "Missing required fields: prompt, mode" },
        { status: 400 }
      );
    }

    const config = readConfig();
    const apiKey = getApiKey();

    if (!apiKey) {
      return NextResponse.json(
        { error: "No API key configured. Add ANTHROPIC_API_KEY to .env.local or set it in Settings." },
        { status: 400 }
      );
    }

    const provider = getProvider({ ...config, apiKey });
    const result = await provider.generateScript(prompt, mode, tone, hooks || 3);

    return NextResponse.json(result);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Unknown error";
    console.error("[AI Generate]", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
