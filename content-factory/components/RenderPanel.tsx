"use client";

import { useState, useEffect, useRef } from "react";
import { StatusBadge } from "./StatusBadge";

interface PipelineStep {
  id: string;
  label: string;
  status: "pending" | "running" | "done" | "error";
}

interface RenderPanelProps {
  mode: string;
}

const ACCENT: Record<string, string> = {
  wealth: "#00D4FF",
  apps: "#22C55E",
  finance: "#D4A843",
  custom: "#8B5CF6",
};

export function RenderPanel({ mode }: RenderPanelProps) {
  const [steps, setSteps] = useState<PipelineStep[]>([
    { id: "pick", label: "Pick Content", status: "pending" },
    { id: "audio", label: "Generate Audio (TTS + Whisper)", status: "pending" },
    { id: "render", label: "Render Video (Remotion)", status: "pending" },
  ]);
  const [logs, setLogs] = useState<string[]>([]);
  const [renderProgress, setRenderProgress] = useState(0);
  const [outputPath, setOutputPath] = useState<string>("");
  const [isRunning, setIsRunning] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const accent = ACCENT[mode] || ACCENT.custom;

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  function addLog(msg: string) {
    setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
  }

  function updateStep(id: string, status: PipelineStep["status"]) {
    setSteps((prev) => prev.map((s) => (s.id === id ? { ...s, status } : s)));
  }

  async function pollJob(url: string, stepId: string): Promise<boolean> {
    while (true) {
      await new Promise((r) => setTimeout(r, 2000));
      const res = await fetch(url);
      const data = await res.json();

      if (data.logs) {
        for (const log of data.logs) {
          addLog(log);
        }
      }

      if (stepId === "render" && data.progress) {
        setRenderProgress(data.progress);
      }

      if (data.status === "done") {
        updateStep(stepId, "done");
        if (data.outputPath) setOutputPath(data.outputPath);
        return true;
      }

      if (data.status === "error") {
        updateStep(stepId, "error");
        addLog(`ERROR: ${data.error || "Unknown error"}`);
        return false;
      }
    }
  }

  async function startPipeline() {
    setIsRunning(true);
    setOutputPath("");
    setRenderProgress(0);
    setLogs([]);
    setSteps([
      { id: "pick", label: "Pick Content", status: "pending" },
      { id: "audio", label: "Generate Audio (TTS + Whisper)", status: "pending" },
      { id: "render", label: "Render Video (Remotion)", status: "pending" },
    ]);

    try {
      // Step 1: Pick content
      updateStep("pick", "running");
      addLog(`Picking content for mode: ${mode}`);
      const pickRes = await fetch("/api/pick", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode }),
      });
      const pickData = await pickRes.json();
      if (!pickRes.ok) throw new Error(pickData.error);
      updateStep("pick", "done");
      addLog(`Picked: ${pickData.data?.script?.title || "unknown"}`);

      // Step 2: Generate audio
      updateStep("audio", "running");
      addLog("Starting TTS generation...");
      const audioRes = await fetch("/api/audio", { method: "POST" });
      const audioData = await audioRes.json();
      if (!audioRes.ok) throw new Error(audioData.error);
      const audioOk = await pollJob(`/api/audio?jobId=${audioData.jobId}`, "audio");
      if (!audioOk) throw new Error("Audio generation failed");
      addLog("Audio generation complete");

      // Step 3: Render video
      updateStep("render", "running");
      addLog("Starting Remotion render...");
      const renderRes = await fetch("/api/render", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode }),
      });
      const renderData = await renderRes.json();
      if (!renderRes.ok) throw new Error(renderData.error);
      const renderOk = await pollJob(`/api/render?jobId=${renderData.jobId}`, "render");
      if (!renderOk) throw new Error("Render failed");
      addLog("Render complete!");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      addLog(`PIPELINE ERROR: ${msg}`);
    }

    setIsRunning(false);
  }

  const allDone = steps.every((s) => s.status === "done");

  return (
    <div className="space-y-6">
      {/* Pipeline steps */}
      <div className="space-y-3">
        {steps.map((step, idx) => (
          <div
            key={step.id}
            className="flex items-center gap-4 p-4 rounded-lg border border-surface-border bg-surface-light"
          >
            <span className="text-lg font-mono text-gray-500 w-6">{idx + 1}</span>
            <div className="flex-1">
              <p className="text-sm font-medium">{step.label}</p>
              {step.id === "render" && step.status === "running" && (
                <div className="mt-2 h-2 rounded-full bg-surface-lighter overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${renderProgress}%`, backgroundColor: accent }}
                  />
                </div>
              )}
            </div>
            <StatusBadge status={step.status} />
          </div>
        ))}
      </div>

      {/* Start button */}
      <button
        onClick={startPipeline}
        disabled={isRunning}
        className="w-full py-3 rounded-lg text-sm font-bold transition-all disabled:opacity-50"
        style={
          isRunning
            ? { backgroundColor: "#333", color: "#888" }
            : { backgroundColor: accent, color: "#000" }
        }
      >
        {isRunning ? "Pipeline Running..." : "Start Full Pipeline"}
      </button>

      {/* Output link */}
      {allDone && outputPath && (
        <div
          className="p-4 rounded-lg border text-sm"
          style={{ borderColor: `${accent}40`, backgroundColor: `${accent}08` }}
        >
          Video rendered successfully! Check the Gallery to view it.
        </div>
      )}

      {/* Log output */}
      {logs.length > 0 && (
        <div className="bg-surface-light border border-surface-border rounded-lg p-4 max-h-64 overflow-y-auto">
          <p className="text-xs text-gray-500 mb-2 uppercase tracking-wider">Pipeline Logs</p>
          <div className="font-mono text-xs space-y-0.5">
            {logs.map((log, i) => (
              <p key={i} className={log.includes("ERROR") ? "text-red-400" : "text-gray-400"}>
                {log}
              </p>
            ))}
            <div ref={logsEndRef} />
          </div>
        </div>
      )}
    </div>
  );
}
