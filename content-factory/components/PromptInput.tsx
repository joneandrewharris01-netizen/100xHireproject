"use client";

import { useState } from "react";

interface PromptInputProps {
  mode: string;
  onGenerate: (prompt: string, tone: string) => void;
  loading: boolean;
}

const TONES = [
  { value: "", label: "Default (mode-specific)" },
  { value: "authoritative", label: "Authoritative" },
  { value: "excited", label: "Excited" },
  { value: "calm", label: "Calm & measured" },
  { value: "conversational", label: "Conversational" },
  { value: "urgent", label: "Urgent" },
];

export function PromptInput({ mode, onGenerate, loading }: PromptInputProps) {
  const [prompt, setPrompt] = useState("");
  const [tone, setTone] = useState("");

  const modeAccents: Record<string, string> = {
    wealth: "#00D4FF",
    apps: "#22C55E",
    finance: "#D4A843",
    custom: "#8B5CF6",
  };
  const accent = modeAccents[mode] || "#00D4FF";

  return (
    <div className="space-y-3">
      <div>
        <label className="block text-xs text-gray-500 uppercase tracking-wider mb-1.5">
          What's this video about?
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={
            mode === "wealth"
              ? "e.g., I built an email-to-sheet automation that saves a client $4K/month..."
              : mode === "apps"
              ? "e.g., A Reddit scraper that finds micro-SaaS ideas with market data..."
              : mode === "finance"
              ? "e.g., Dubai's 0% income tax — what freelancers actually need to know..."
              : "Describe your video concept..."
          }
          rows={4}
          className="w-full bg-surface border border-surface-border rounded-lg p-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-gray-500 resize-none"
        />
      </div>

      <div className="flex gap-3 items-end">
        <div className="flex-1">
          <label className="block text-xs text-gray-500 uppercase tracking-wider mb-1.5">
            Tone
          </label>
          <select
            value={tone}
            onChange={(e) => setTone(e.target.value)}
            className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
          >
            {TONES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={() => prompt.trim() && onGenerate(prompt.trim(), tone)}
          disabled={!prompt.trim() || loading}
          className="px-6 py-2 rounded-lg text-sm font-bold transition-all disabled:opacity-40"
          style={{ backgroundColor: accent, color: "#000" }}
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Generating...
            </span>
          ) : (
            "Generate Script"
          )}
        </button>
      </div>
    </div>
  );
}
