import { NextResponse } from "next/server";
import { readConfig, writeConfig } from "../../../lib/config";

export async function GET() {
  const config = readConfig();
  // Mask the API key for security
  return NextResponse.json({
    ...config,
    apiKey: config.apiKey ? `${config.apiKey.slice(0, 10)}...${config.apiKey.slice(-4)}` : "",
    hasKey: !!config.apiKey || !!process.env.ANTHROPIC_API_KEY,
  });
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const updated = writeConfig(body);
    return NextResponse.json({
      ...updated,
      apiKey: updated.apiKey ? `${updated.apiKey.slice(0, 10)}...${updated.apiKey.slice(-4)}` : "",
      hasKey: !!updated.apiKey,
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Failed to save settings";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
