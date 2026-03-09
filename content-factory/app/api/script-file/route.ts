import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const ROOT = process.cwd();

// GET /api/script-file?mode=wealth&file=001-email-automation.json
export async function GET(req: NextRequest) {
  const mode = req.nextUrl.searchParams.get("mode");
  const file = req.nextUrl.searchParams.get("file");

  if (!mode || !file) {
    return NextResponse.json({ error: "Missing mode or file" }, { status: 400 });
  }

  const safeName = path.basename(file);
  const filePath = path.join(ROOT, "content", mode, safeName);

  if (!fs.existsSync(filePath)) {
    return NextResponse.json({ error: "File not found" }, { status: 404 });
  }

  const raw = fs.readFileSync(filePath, "utf-8");
  const data = JSON.parse(raw);
  return NextResponse.json(data);
}
