"use client";

import { useEffect, useState } from "react";
import { VideoPreview } from "../../components/VideoPreview";

const MODES = [
  { mode: "wealth", label: "Wealth", accent: "#00D4FF" },
  { mode: "apps", label: "Apps", accent: "#22C55E" },
  { mode: "finance", label: "Finance", accent: "#D4A843" },
  { mode: "custom", label: "Custom", accent: "#8B5CF6" },
];

export default function PreviewPage() {
  const [todayData, setTodayData] = useState<Record<string, unknown> | null>(null);
  const [selectedMode, setSelectedMode] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [generatingAudio, setGeneratingAudio] = useState(false);

  useEffect(() => {
    fetchToday();
  }, []);

  async function fetchToday() {
    setLoading(true);
    try {
      const res = await fetch("/api/today");
      if (res.ok) {
        const data = await res.json();
        setTodayData(data);
        const script = data.script as { mode?: string } | undefined;
        if (script?.mode) {
          setSelectedMode(script.mode);
        }
      }
    } catch {
      // ignore
    }
    setLoading(false);
  }

  async function handleGenerateAudio() {
    setGeneratingAudio(true);
    try {
      const res = await fetch("/api/audio", { method: "POST" });
      const { jobId } = await res.json();

      // Poll for completion
      while (true) {
        await new Promise((r) => setTimeout(r, 2000));
        const statusRes = await fetch(`/api/audio?jobId=${jobId}`);
        const statusData = await statusRes.json();

        if (statusData.status === "done") {
          await fetchToday(); // Reload with audio data
          break;
        }
        if (statusData.status === "error") {
          alert(`Audio generation failed: ${statusData.error}`);
          break;
        }
      }
    } catch {
      alert("Audio generation failed");
    }
    setGeneratingAudio(false);
  }

  const script = todayData?.script as { title?: string; hook?: string; mode?: string; scenes?: unknown[] } | undefined;
  const audio = todayData?.audio as { audioFile?: string; durationSeconds?: number; words?: unknown[] } | undefined;
  const hasAudio = !!audio?.audioFile;
  const currentAccent = MODES.find((m) => m.mode === selectedMode)?.accent || "#666";

  return (
    <div className="h-[calc(100vh-3rem)] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold mb-1">Preview</h2>
          <p className="text-gray-400 text-sm">Live Remotion Player — current today.json content.</p>
        </div>

        {/* Mode selector */}
        <select
          value={selectedMode}
          onChange={(e) => setSelectedMode(e.target.value)}
          className="bg-surface-light border border-surface-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
        >
          {MODES.map((m) => (
            <option key={m.mode} value={m.mode}>
              {m.label}Video
            </option>
          ))}
        </select>
      </div>

      <div className="flex-1 flex gap-6 min-h-0">
        {/* Player */}
        <div className="flex-1 bg-surface-light border border-surface-border rounded-xl overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-full text-gray-500">Loading...</div>
          ) : (
            <VideoPreview mode={selectedMode} data={todayData} />
          )}
        </div>

        {/* Side panel */}
        <div className="w-72 shrink-0 space-y-4 overflow-y-auto">
          {/* Current script info */}
          <div className="p-4 rounded-lg border border-surface-border bg-surface-light">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Current Script</p>
            {script ? (
              <>
                <p className="text-sm font-medium mb-1">{script.title || "Untitled"}</p>
                <p className="text-xs text-gray-400 mb-2">{script.hook}</p>
                <div className="flex gap-2 text-xs">
                  <span
                    className="px-2 py-0.5 rounded-full font-mono"
                    style={{ backgroundColor: `${currentAccent}20`, color: currentAccent }}
                  >
                    {script.mode}
                  </span>
                  <span className="text-gray-500">{script.scenes?.length || 0} scenes</span>
                </div>
              </>
            ) : (
              <p className="text-sm text-gray-500">No script loaded</p>
            )}
          </div>

          {/* Audio status */}
          <div className="p-4 rounded-lg border border-surface-border bg-surface-light">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Audio</p>
            {hasAudio ? (
              <div className="space-y-1">
                <p className="text-sm text-green-400">Audio ready</p>
                <p className="text-xs text-gray-500">
                  {audio?.durationSeconds?.toFixed(1)}s / {(audio?.words as unknown[])?.length || 0} words
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-sm text-yellow-400">No audio generated</p>
                <button
                  onClick={handleGenerateAudio}
                  disabled={generatingAudio || !script}
                  className="w-full py-2 rounded-md text-xs font-bold transition-colors disabled:opacity-50"
                  style={{ backgroundColor: currentAccent, color: "#000" }}
                >
                  {generatingAudio ? "Generating..." : "Generate Audio"}
                </button>
              </div>
            )}
          </div>

          {/* Quick links */}
          <div className="space-y-2">
            <a
              href="/brand"
              className="block w-full py-2 rounded-lg text-sm font-medium text-center border transition-colors"
              style={{ borderColor: currentAccent, color: currentAccent }}
            >
              Open Brand Designer
            </a>
            <button
              onClick={fetchToday}
              className="w-full py-2 rounded-lg text-sm font-medium bg-surface-lighter text-gray-300 hover:text-white border border-surface-border transition-colors"
            >
              Refresh Data
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
