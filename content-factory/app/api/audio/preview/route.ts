import { NextResponse } from "next/server";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const PYTHON = "C:\\Users\\Admin\\AppData\\Local\\Programs\\Python\\Python311\\python.exe";
const ROOT = process.cwd();
const PREVIEW_PATH = path.join(ROOT, "public", "audio", "preview.mp3");

export async function POST(req: Request) {
  try {
    const { text, voice, rate, pitch } = await req.json();

    if (!text) {
      return NextResponse.json({ error: "Missing text" }, { status: 400 });
    }

    // Truncate to ~20 words for a short preview
    const words = text.split(/\s+/).slice(0, 20).join(" ");

    // Ensure output directory exists
    const audioDir = path.dirname(PREVIEW_PATH);
    if (!fs.existsSync(audioDir)) {
      fs.mkdirSync(audioDir, { recursive: true });
    }

    // Build edge-tts command args
    const args = [
      "-m", "edge_tts",
      "--voice", voice || "en-US-GuyNeural",
      "--rate", rate || "+15%",
      "--pitch", pitch || "+0Hz",
      "--text", words,
      "--write-media", PREVIEW_PATH,
    ];

    return new Promise<Response>((resolve) => {
      const proc = spawn(PYTHON, args, { cwd: ROOT, stdio: ["ignore", "pipe", "pipe"] });

      let stderr = "";
      proc.stderr.on("data", (chunk: Buffer) => { stderr += chunk.toString("utf-8"); });

      proc.on("close", (code) => {
        if (code === 0) {
          resolve(
            NextResponse.json({
              url: `/audio/preview.mp3?t=${Date.now()}`,
              words: words,
            })
          );
        } else {
          resolve(
            NextResponse.json({ error: `TTS failed: ${stderr}` }, { status: 500 })
          );
        }
      });
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
