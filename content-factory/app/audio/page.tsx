"use client";

import { useEffect, useState, useRef } from "react";
import { VoicePicker } from "../../components/VoicePicker";
import { AudioSliders } from "../../components/AudioSliders";
import { WaveformDisplay } from "../../components/WaveformDisplay";
import { WordTimeline } from "../../components/WordTimeline";

const MODE_ACCENTS: Record<string, string> = {
  wealth: "#00D4FF",
  apps: "#22C55E",
  finance: "#D4A843",
  custom: "#8B5CF6",
};

const MODE_VOICES: Record<string, { id: string; rate: string; pitch: string }> = {
  wealth: { id: "en-US-GuyNeural", rate: "+18%", pitch: "+0Hz" },
  apps: { id: "en-US-AndrewNeural", rate: "+15%", pitch: "+0Hz" },
  finance: { id: "en-US-BrianNeural", rate: "+10%", pitch: "+0Hz" },
  custom: { id: "en-US-GuyNeural", rate: "+15%", pitch: "+0Hz" },
};

interface WordTimestamp {
  word: string;
  start: number;
  end: number;
}

export default function AudioPage() {
  const [todayData, setTodayData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  // Voice settings
  const [voice, setVoice] = useState("en-US-GuyNeural");
  const [rate, setRate] = useState("+15%");
  const [pitch, setPitch] = useState("+0Hz");

  // Audio state
  const [generating, setGenerating] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [words, setWords] = useState<WordTimestamp[]>([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [voText, setVoText] = useState("");
  const [editingVo, setEditingVo] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const script = todayData?.script as {
    title?: string;
    hook?: string;
    mode?: string;
    voiceoverScript?: string;
    scenes?: unknown[];
  } | undefined;

  const mode = script?.mode || "wealth";
  const accent = MODE_ACCENTS[mode] || "#00D4FF";

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

        const s = data.script as { mode?: string; voiceoverScript?: string };
        if (s?.mode) {
          const defaults = MODE_VOICES[s.mode] || MODE_VOICES.custom;
          setVoice(defaults.id);
          setRate(defaults.rate);
          setPitch(defaults.pitch);
        }
        if (s?.voiceoverScript) {
          setVoText(s.voiceoverScript);
        }

        // Check if audio already exists
        const audio = data.audio as { audioFile?: string; words?: WordTimestamp[] };
        if (audio?.audioFile) {
          setAudioUrl(`/${audio.audioFile}?t=${Date.now()}`);
          if (audio.words) setWords(audio.words);
        }
      }
    } catch {
      // ignore
    }
    setLoading(false);
  }

  async function handlePreview() {
    try {
      const res = await fetch("/api/audio/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: voText || script?.voiceoverScript || "Hello, this is a test.",
          voice,
          rate,
          pitch,
        }),
      });
      const data = await res.json();
      if (data.url) {
        const audio = new Audio(data.url);
        audio.play().catch(() => {});
      }
    } catch {
      alert("Preview failed");
    }
  }

  async function handleGenerateFull() {
    setGenerating(true);
    try {
      const res = await fetch("/api/audio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ voice, rate, pitch }),
      });
      const { jobId } = await res.json();

      // Poll for completion
      while (true) {
        await new Promise((r) => setTimeout(r, 2000));
        const statusRes = await fetch(`/api/audio?jobId=${jobId}`);
        const statusData = await statusRes.json();

        if (statusData.status === "done") {
          // Reload data
          await fetchToday();
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
    setGenerating(false);
  }

  // Track audio playback time for word timeline
  useEffect(() => {
    const interval = setInterval(() => {
      if (audioRef.current && !audioRef.current.paused) {
        setCurrentTime(audioRef.current.currentTime);
      }
    }, 50);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">Loading...</div>
    );
  }

  return (
    <div className="h-[calc(100vh-3rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold mb-1">Audio Studio</h2>
          <p className="text-gray-400 text-sm">
            Pick a voice, tune rate & pitch, preview, and generate audio.
          </p>
        </div>
        <span
          className="px-3 py-1 rounded-full text-xs font-bold"
          style={{ backgroundColor: `${accent}20`, color: accent }}
        >
          {mode}
        </span>
      </div>

      {/* Main layout */}
      <div className="flex-1 flex gap-6 min-h-0 overflow-hidden">
        {/* Left column: controls */}
        <div className="w-72 shrink-0 space-y-4 overflow-y-auto">
          <div className="p-4 rounded-xl border border-surface-border bg-surface-light space-y-4">
            <VoicePicker value={voice} onChange={setVoice} accent={accent} />
            <AudioSliders
              rate={rate}
              pitch={pitch}
              onRateChange={setRate}
              onPitchChange={setPitch}
              accent={accent}
            />
          </div>

          <div className="space-y-2">
            <button
              onClick={handlePreview}
              className="w-full py-2 rounded-lg text-sm font-medium border transition-colors"
              style={{ borderColor: accent, color: accent }}
            >
              Preview 5s Clip
            </button>
            <button
              onClick={handleGenerateFull}
              disabled={generating}
              className="w-full py-2.5 rounded-lg text-sm font-bold transition-colors disabled:opacity-50"
              style={{ backgroundColor: accent, color: "#000" }}
            >
              {generating ? "Generating..." : "Generate Full Audio"}
            </button>
          </div>
        </div>

        {/* Right column: waveform + timeline + script */}
        <div className="flex-1 space-y-4 overflow-y-auto">
          <WaveformDisplay audioUrl={audioUrl} accent={accent} />
          <WordTimeline words={words} currentTime={currentTime} accent={accent} />

          {/* Current script */}
          <div className="p-4 rounded-xl border border-surface-border bg-surface-light">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs text-gray-500 uppercase tracking-wider">
                Current Script: "{script?.title || "No script loaded"}"
              </p>
              <button
                onClick={() => {
                  if (editingVo) {
                    // Could save back voiceover edits to today.json via API
                  }
                  setEditingVo(!editingVo);
                }}
                className="text-xs transition-colors"
                style={{ color: accent }}
              >
                {editingVo ? "Done" : "Edit"}
              </button>
            </div>
            {editingVo ? (
              <textarea
                value={voText}
                onChange={(e) => setVoText(e.target.value)}
                rows={4}
                className="w-full bg-surface border border-surface-border rounded-lg p-3 text-sm text-white focus:outline-none resize-none"
              />
            ) : (
              <p className="text-sm text-gray-300 leading-relaxed">
                {voText || script?.voiceoverScript || "No voiceover text loaded."}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
