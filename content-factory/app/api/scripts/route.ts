import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const ROOT = process.cwd();

function getContentDir(mode: string) {
  return path.join(ROOT, "content", mode);
}

// GET /api/scripts?mode=wealth — list scripts for a mode
export async function GET(req: NextRequest) {
  const mode = req.nextUrl.searchParams.get("mode") || "wealth";
  const validModes = ["wealth", "apps", "finance", "custom"];

  if (!validModes.includes(mode)) {
    return NextResponse.json({ error: `Invalid mode: ${mode}` }, { status: 400 });
  }

  const dir = getContentDir(mode);
  if (!fs.existsSync(dir)) {
    return NextResponse.json({ scripts: [] });
  }

  const files = fs.readdirSync(dir).filter((f) => f.endsWith(".json"));
  const scripts = files.map((filename) => {
    const filePath = path.join(dir, filename);
    try {
      const raw = fs.readFileSync(filePath, "utf-8");
      const data = JSON.parse(raw);
      return {
        filename,
        id: data.id || filename.replace(".json", ""),
        title: data.title || "Untitled",
        hook: data.hook || "",
        sceneCount: data.scenes?.length || 0,
        mode: data.mode || mode,
      };
    } catch {
      return { filename, id: filename, title: "Parse Error", hook: "", sceneCount: 0, mode };
    }
  });

  return NextResponse.json({ scripts, mode });
}

// POST /api/scripts — save a script
export async function POST(req: NextRequest) {
  const body = await req.json();
  const { mode, filename, content } = body;

  if (!mode || !filename || !content) {
    return NextResponse.json(
      { error: "Missing mode, filename, or content" },
      { status: 400 }
    );
  }

  const dir = getContentDir(mode);
  fs.mkdirSync(dir, { recursive: true });

  const safeName = filename.replace(/[^a-zA-Z0-9_\-\.]/g, "");
  const filePath = path.join(dir, safeName.endsWith(".json") ? safeName : `${safeName}.json`);

  fs.writeFileSync(filePath, JSON.stringify(content, null, 2), "utf-8");

  return NextResponse.json({ ok: true, path: filePath });
}

// DELETE /api/scripts?mode=wealth&file=001-email-automation.json
export async function DELETE(req: NextRequest) {
  const mode = req.nextUrl.searchParams.get("mode");
  const file = req.nextUrl.searchParams.get("file");

  if (!mode || !file) {
    return NextResponse.json({ error: "Missing mode or file" }, { status: 400 });
  }

  const filePath = path.join(getContentDir(mode), file);
  if (!fs.existsSync(filePath)) {
    return NextResponse.json({ error: "File not found" }, { status: 404 });
  }

  fs.unlinkSync(filePath);
  return NextResponse.json({ ok: true });
}
