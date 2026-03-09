import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const ROOT = process.cwd();

// In-memory job store for renders
const renderJobs = new Map<
  string,
  { status: string; logs: string[]; error?: string; outputPath?: string; mode: string }
>();

// POST /api/render — start a full render pipeline
// Body: { mode: "wealth" }
export async function POST(req: NextRequest) {
  const body = await req.json();
  const { mode } = body;

  if (!mode) {
    return NextResponse.json({ error: "Missing mode" }, { status: 400 });
  }

  const compositionMap: Record<string, string> = {
    wealth: "WealthVideo",
    apps: "AppsVideo",
    finance: "FinanceVideo",
    custom: "CustomVideo",
  };

  const compositionId = compositionMap[mode];
  if (!compositionId) {
    return NextResponse.json({ error: `Invalid mode: ${mode}` }, { status: 400 });
  }

  const jobId = `render-${mode}-${Date.now()}`;
  const outputDir = path.join(ROOT, "out", mode);
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const outputFile = path.join(outputDir, `${mode}-${timestamp}.mp4`);

  fs.mkdirSync(outputDir, { recursive: true });

  renderJobs.set(jobId, { status: "running", logs: [], mode });

  // Run the full Remotion render
  const proc = spawn(
    "npx",
    [
      "remotion",
      "render",
      "src/index.ts",
      compositionId,
      outputFile,
      "--codec",
      "h264",
      "--crf",
      "18",
    ],
    {
      cwd: ROOT,
      stdio: ["ignore", "pipe", "pipe"],
      shell: true,
    }
  );

  proc.stdout.on("data", (chunk: Buffer) => {
    const job = renderJobs.get(jobId);
    if (job) {
      const text = chunk.toString("utf-8").trim();
      if (text) job.logs.push(text);
    }
  });

  proc.stderr.on("data", (chunk: Buffer) => {
    const job = renderJobs.get(jobId);
    if (job) {
      const text = chunk.toString("utf-8").trim();
      if (text) job.logs.push(text);
    }
  });

  proc.on("close", (code) => {
    const job = renderJobs.get(jobId);
    if (job) {
      job.status = code === 0 ? "done" : "error";
      if (code === 0) {
        job.outputPath = outputFile;
      } else {
        job.error = `Render exited with code ${code}`;
      }
    }
  });

  return NextResponse.json({ jobId, status: "running", mode });
}

// GET /api/render?jobId=xxx — check render status
export async function GET(req: NextRequest) {
  const jobId = req.nextUrl.searchParams.get("jobId");

  if (!jobId) {
    return NextResponse.json({ error: "Missing jobId" }, { status: 400 });
  }

  const job = renderJobs.get(jobId);
  if (!job) {
    return NextResponse.json({ error: "Job not found" }, { status: 404 });
  }

  // Extract progress % from Remotion logs if available
  let progress = 0;
  for (const log of job.logs) {
    const match = log.match(/(\d+)%/);
    if (match) {
      progress = Math.max(progress, parseInt(match[1], 10));
    }
  }

  return NextResponse.json({
    jobId,
    status: job.status,
    mode: job.mode,
    progress,
    logs: job.logs.slice(-20), // last 20 log lines
    error: job.error,
    outputPath: job.outputPath,
  });
}
