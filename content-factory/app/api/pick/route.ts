import { NextRequest, NextResponse } from "next/server";
import { execSync } from "child_process";
import fs from "fs";
import path from "path";

const PYTHON = "C:\\Users\\Admin\\AppData\\Local\\Programs\\Python\\Python311\\python.exe";
const ROOT = process.cwd();
const TODAY_JSON = path.join(ROOT, "src", "data", "today.json");

// POST /api/pick — pick content into today.json
// Body: { mode: "wealth", file?: "content/wealth/001-email-automation.json" }
export async function POST(req: NextRequest) {
  const body = await req.json();
  const { mode, file } = body;

  if (!mode) {
    return NextResponse.json({ error: "Missing mode" }, { status: 400 });
  }

  const validModes = ["wealth", "apps", "finance", "custom"];
  if (!validModes.includes(mode)) {
    return NextResponse.json({ error: `Invalid mode: ${mode}` }, { status: 400 });
  }

  try {
    let cmd = `"${PYTHON}" scripts/pick-content.py --mode ${mode}`;
    if (file) {
      cmd += ` --file "${file}"`;
    }

    execSync(cmd, { cwd: ROOT, stdio: "pipe", encoding: "utf-8" });

    const raw = fs.readFileSync(TODAY_JSON, "utf-8");
    const data = JSON.parse(raw);

    return NextResponse.json({ ok: true, data });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
