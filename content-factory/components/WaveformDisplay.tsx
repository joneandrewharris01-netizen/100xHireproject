"use client";

import { useRef, useEffect, useState } from "react";

interface WaveformDisplayProps {
  audioUrl: string | null;
  accent?: string;
}

export function WaveformDisplay({ audioUrl, accent = "#00D4FF" }: WaveformDisplayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const animFrameRef = useRef<number>(0);
  const waveDataRef = useRef<Float32Array | null>(null);

  useEffect(() => {
    if (!audioUrl) return;

    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    audio.addEventListener("loadedmetadata", () => setDuration(audio.duration));
    audio.addEventListener("ended", () => setPlaying(false));

    // Decode audio for waveform
    fetch(audioUrl)
      .then((r) => r.arrayBuffer())
      .then((buf) => {
        const ctx = new AudioContext();
        return ctx.decodeAudioData(buf);
      })
      .then((decoded) => {
        waveDataRef.current = decoded.getChannelData(0);
        drawWaveform();
      })
      .catch(() => {});

    return () => {
      audio.pause();
      cancelAnimationFrame(animFrameRef.current);
    };
  }, [audioUrl]);

  // Update time display during playback
  useEffect(() => {
    if (!playing) return;
    const tick = () => {
      if (audioRef.current) {
        setCurrentTime(audioRef.current.currentTime);
        drawWaveform(audioRef.current.currentTime / audioRef.current.duration);
      }
      animFrameRef.current = requestAnimationFrame(tick);
    };
    animFrameRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [playing]);

  function drawWaveform(progress: number = 0) {
    const canvas = canvasRef.current;
    const data = waveDataRef.current;
    if (!canvas || !data) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const { width, height } = canvas;
    ctx.clearRect(0, 0, width, height);

    const barCount = 80;
    const barWidth = width / barCount - 1;
    const samplesPerBar = Math.floor(data.length / barCount);

    for (let i = 0; i < barCount; i++) {
      let sum = 0;
      const start = i * samplesPerBar;
      for (let j = start; j < start + samplesPerBar; j++) {
        sum += Math.abs(data[j] || 0);
      }
      const avg = sum / samplesPerBar;
      const barHeight = Math.max(2, avg * height * 2);

      const isPast = i / barCount < progress;
      ctx.fillStyle = isPast ? accent : `${accent}40`;

      const x = i * (barWidth + 1);
      const y = (height - barHeight) / 2;
      ctx.fillRect(x, y, barWidth, barHeight);
    }
  }

  function togglePlay() {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
      setPlaying(false);
    } else {
      audioRef.current.play().catch(() => {});
      setPlaying(true);
    }
  }

  function formatTime(s: number): string {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  }

  if (!audioUrl) {
    return (
      <div className="rounded-lg border border-surface-border bg-surface-light p-6 flex items-center justify-center">
        <p className="text-sm text-gray-500">No audio generated yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <label className="block text-xs text-gray-500 uppercase tracking-wider">Waveform</label>
      <div className="rounded-lg border border-surface-border bg-surface-light p-4">
        <canvas
          ref={canvasRef}
          width={400}
          height={80}
          className="w-full h-20 rounded"
          style={{ background: "#0A0E16" }}
        />
        <div className="flex items-center justify-between mt-2">
          <button
            onClick={togglePlay}
            className="flex items-center gap-1.5 text-xs font-medium transition-colors"
            style={{ color: accent }}
          >
            {playing ? (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="4" width="4" height="16" />
                <rect x="14" y="4" width="4" height="16" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
            {playing ? "Pause" : "Play"}
          </button>
          <span className="text-xs text-gray-500 font-mono">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>
      </div>
    </div>
  );
}
