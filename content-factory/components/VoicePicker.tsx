"use client";

import { useEffect, useState } from "react";

interface Voice {
  id: string;
  name: string;
  gender: string;
  locale: string;
}

interface VoicePickerProps {
  value: string;
  onChange: (voiceId: string) => void;
  accent?: string;
}

export function VoicePicker({ value, onChange, accent = "#00D4FF" }: VoicePickerProps) {
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loading, setLoading] = useState(true);
  const [playing, setPlaying] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/audio/voices")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) setVoices(data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const maleVoices = voices.filter((v) => v.gender === "Male");
  const femaleVoices = voices.filter((v) => v.gender === "Female");

  async function handlePreview(voiceId: string) {
    setPlaying(voiceId);
    try {
      const res = await fetch("/api/audio/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: "This is a sample of my voice. How does it sound for your video?",
          voice: voiceId,
          rate: "+15%",
          pitch: "+0Hz",
        }),
      });
      const data = await res.json();
      if (data.url) {
        const audio = new Audio(data.url);
        audio.onended = () => setPlaying(null);
        audio.play().catch(() => setPlaying(null));
      }
    } catch {
      setPlaying(null);
    }
  }

  if (loading) {
    return (
      <div className="text-sm text-gray-500 py-2">Loading voices...</div>
    );
  }

  return (
    <div className="space-y-2">
      <label className="block text-xs text-gray-500 uppercase tracking-wider">Voice</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
      >
        <optgroup label="Male">
          {maleVoices.map((v) => (
            <option key={v.id} value={v.id}>
              {v.name} ({v.locale})
            </option>
          ))}
        </optgroup>
        <optgroup label="Female">
          {femaleVoices.map((v) => (
            <option key={v.id} value={v.id}>
              {v.name} ({v.locale})
            </option>
          ))}
        </optgroup>
      </select>

      <button
        onClick={() => handlePreview(value)}
        disabled={playing === value}
        className="text-xs px-3 py-1 rounded transition-colors"
        style={{ color: accent, borderColor: accent, border: "1px solid" }}
      >
        {playing === value ? "Playing..." : "Preview voice"}
      </button>
    </div>
  );
}
