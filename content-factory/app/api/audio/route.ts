import { NextResponse } from "next/server";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const PYTHON = "C:\\Users\\Admin\\AppData\\Local\\Programs\\Python\\Python311\\python.exe";
const ROOT = process.cwd();
const TODAY_JSON = path.join(ROOT, "src", "data", "today.json");

// In-memory job store for audio generation
const audioJobs = new Map<string, { status: string; logs: string[]; error?: string }>();

// POST /api/audio — generate TTS + timestamps
export async function POST(req: Request) {
  const jobId = `audio-${Date.now()}`;
  audioJobs.set(jobId, { status: "running", logs: [] });

  // Accept optional custom voice params
  let voice: string | undefined;
  let rate: string | undefined;
  let pitch: string | undefined;
  try {
    const body = await req.json();
    voice = body.voice;
    rate = body.rate;
    pitch = body.pitch;
  } catch {
    // No body — use defaults from generate-audio-custom.py / generate-audio.py
  }

  // Use custom script if voice params provided, otherwise original
  const scriptFile = (voice || rate || pitch)
    ? "scripts/generate-audio-custom.py"
    : "scripts/generate-audio.py";
  const args = [scriptFile];
  if (voice) { args.push("--voice", voice); }
  if (rate) { args.push("--rate", rate); }
  if (pitch) { args.push("--pitch", pitch); }

  const proc = spawn(PYTHON, args, {
    cwd: ROOT,
    stdio: ["ignore", "pipe", "pipe"],
  });

  proc.stdout.on("data", (chunk: Buffer) => {
    const job = audioJobs.get(jobId);
    if (job) job.logs.push(chunk.toString("utf-8").trim());
  });

  proc.stderr.on("data", (chunk: Buffer) => {
    const job = audioJobs.get(jobId);
    if (job) job.logs.push(`[stderr] ${chunk.toString("utf-8").trim()}`);
  });

  proc.on("close", (code) => {
    const job = audioJobs.get(jobId);
    if (job) {
      job.status = code === 0 ? "done" : "error";
      if (code !== 0) job.error = `Process exited with code ${code}`;
    }
  });

  return NextResponse.json({ jobId, status: "running" });
}

// GET /api/audio?jobId=xxx — check audio generation status
export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const jobId = searchParams.get("jobId");

  if (!jobId) {
    return NextResponse.json({ error: "Missing jobId" }, { status: 400 });
  }

  const job = audioJobs.get(jobId);
  if (!job) {
    return NextResponse.json({ error: "Job not found" }, { status: 404 });
  }

  let todayData = null;
  if (job.status === "done") {
    try {
      const raw = fs.readFileSync(TODAY_JSON, "utf-8");
      todayData = JSON.parse(raw);
    } catch { /* ignore */ }
  }

  return NextResponse.json({
    jobId,
    status: job.status,
    logs: job.logs,
    error: job.error,
    data: todayData,
  });
}
