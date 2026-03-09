import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const ROOT = process.cwd();

// GET /api/outputs?mode=wealth — list rendered videos
export async function GET(req: NextRequest) {
  const mode = req.nextUrl.searchParams.get("mode");
  const validModes = ["wealth", "apps", "finance", "custom"];

  // If mode specified, list only that mode's outputs
  const modes = mode && validModes.includes(mode) ? [mode] : validModes;

  const outputs: {
    filename: string;
    mode: string;
    path: string;
    size: number;
    sizeFormatted: string;
    createdAt: string;
  }[] = [];

  for (const m of modes) {
    const dir = path.join(ROOT, "out", m);
    if (!fs.existsSync(dir)) continue;

    const files = fs.readdirSync(dir).filter((f) => f.endsWith(".mp4"));
    for (const filename of files) {
      const filePath = path.join(dir, filename);
      const stat = fs.statSync(filePath);
      outputs.push({
        filename,
        mode: m,
        path: `/api/outputs/video?mode=${m}&file=${encodeURIComponent(filename)}`,
        size: stat.size,
        sizeFormatted: formatSize(stat.size),
        createdAt: stat.birthtime.toISOString(),
      });
    }
  }

  // Sort by creation date, newest first
  outputs.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

  return NextResponse.json({ outputs });
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
