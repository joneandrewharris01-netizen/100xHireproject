import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const BRANDS_DIR = path.join(process.cwd(), "brands");

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const mode = searchParams.get("mode");

    if (!mode) {
      // List all brand profiles
      const files = fs.readdirSync(BRANDS_DIR).filter((f) => f.endsWith(".json"));
      const profiles = files.map((f) => {
        const raw = fs.readFileSync(path.join(BRANDS_DIR, f), "utf-8");
        return JSON.parse(raw);
      });
      return NextResponse.json(profiles);
    }

    // Find brand for specific mode (prefer custom, fall back to default)
    const files = fs.readdirSync(BRANDS_DIR).filter((f) => f.endsWith(".json"));
    const modeFiles = files.filter((f) => f.startsWith(mode));

    // Prefer custom over default
    const customFile = modeFiles.find((f) => !f.includes("-default"));
    const defaultFile = modeFiles.find((f) => f.includes("-default"));
    const targetFile = customFile || defaultFile;

    if (!targetFile) {
      return NextResponse.json({ error: `No brand profile for mode: ${mode}` }, { status: 404 });
    }

    const raw = fs.readFileSync(path.join(BRANDS_DIR, targetFile), "utf-8");
    return NextResponse.json(JSON.parse(raw));
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const { mode, profile } = await req.json();

    if (!mode || !profile) {
      return NextResponse.json({ error: "Missing mode or profile" }, { status: 400 });
    }

    const safeName = (profile.name || mode)
      .toLowerCase()
      .replace(/[^a-z0-9-]/g, "-")
      .replace(/-+/g, "-");
    const filename = `${mode}-${safeName}.json`;
    const filepath = path.join(BRANDS_DIR, filename);

    if (!fs.existsSync(BRANDS_DIR)) {
      fs.mkdirSync(BRANDS_DIR, { recursive: true });
    }

    fs.writeFileSync(filepath, JSON.stringify(profile, null, 2), "utf-8");

    return NextResponse.json({ saved: filename, profile });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
