import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const ROOT = process.cwd();

// GET /api/outputs/video?mode=wealth&file=video.mp4 — serve a rendered video
export async function GET(req: NextRequest) {
  const mode = req.nextUrl.searchParams.get("mode");
  const file = req.nextUrl.searchParams.get("file");

  if (!mode || !file) {
    return NextResponse.json({ error: "Missing mode or file" }, { status: 400 });
  }

  // Prevent path traversal
  const safeName = path.basename(file);
  const filePath = path.join(ROOT, "out", mode, safeName);

  if (!fs.existsSync(filePath)) {
    return NextResponse.json({ error: "File not found" }, { status: 404 });
  }

  const stat = fs.statSync(filePath);
  const buffer = fs.readFileSync(filePath);

  return new NextResponse(buffer, {
    headers: {
      "Content-Type": "video/mp4",
      "Content-Length": stat.size.toString(),
      "Content-Disposition": `inline; filename="${safeName}"`,
    },
  });
}
