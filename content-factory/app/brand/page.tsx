"use client";

import { useEffect, useState } from "react";
import { ColorPicker } from "../../components/ColorPicker";
import { FontSelector } from "../../components/FontSelector";
import { AnimationPicker } from "../../components/AnimationPicker";
import { BrandPreview } from "../../components/BrandPreview";

type ContentMode = "wealth" | "apps" | "finance" | "custom";

interface BrandProfile {
  name: string;
  mode: string;
  badge: string;
  colors: {
    accent: string;
    accentLight: string;
    accentDark: string;
    bg: string;
    text: string;
    textSoft: string;
    termBg: string;
    termBorder: string;
  };
  fonts: {
    heading: string;
    body: string;
    mono: string;
  };
  captions: {
    fontSize: number;
    activeFontSize: number;
    top: number;
  };
  voice: {
    id: string;
    rate: string;
    pitch: string;
  };
  animation: string;
}

const MODES: { mode: ContentMode; label: string; accent: string }[] = [
  { mode: "wealth", label: "Wealth", accent: "#00D4FF" },
  { mode: "apps", label: "Apps", accent: "#22C55E" },
  { mode: "finance", label: "Finance", accent: "#D4A843" },
  { mode: "custom", label: "Custom", accent: "#8B5CF6" },
];

const ACCENT_PRESETS = ["#00D4FF", "#22C55E", "#D4A843", "#8B5CF6", "#FF6B9D", "#FF4444", "#FFD700", "#00FF88"];

export default function BrandPage() {
  const [mode, setMode] = useState<ContentMode>("wealth");
  const [profile, setProfile] = useState<BrandProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const accent = MODES.find((m) => m.mode === mode)?.accent || "#00D4FF";

  useEffect(() => {
    loadBrand(mode);
  }, [mode]);

  async function loadBrand(m: string) {
    setLoading(true);
    try {
      const res = await fetch(`/api/brand?mode=${m}`);
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
      }
    } catch {
      // ignore
    }
    setLoading(false);
  }

  async function handleSave() {
    if (!profile) return;
    setSaving(true);
    try {
      const res = await fetch("/api/brand", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, profile }),
      });
      if (res.ok) {
        alert("Brand profile saved!");
      }
    } catch {
      alert("Failed to save brand profile");
    }
    setSaving(false);
  }

  function update(path: string, value: unknown) {
    if (!profile) return;
    const updated = JSON.parse(JSON.stringify(profile));
    const parts = path.split(".");
    let obj = updated as Record<string, unknown>;
    for (let i = 0; i < parts.length - 1; i++) {
      obj = obj[parts[i]] as Record<string, unknown>;
    }
    obj[parts[parts.length - 1]] = value;
    setProfile(updated);
  }

  if (loading || !profile) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">Loading brand...</div>
    );
  }

  return (
    <div className="h-[calc(100vh-3rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold mb-1">Brand Designer</h2>
          <p className="text-gray-400 text-sm">
            Customize colors, fonts, captions, and animation styles per mode.
          </p>
        </div>
      </div>

      {/* Mode tabs */}
      <div className="flex gap-1 mb-4">
        {MODES.map((m) => (
          <button
            key={m.mode}
            onClick={() => setMode(m.mode)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
              mode === m.mode ? "text-black" : "text-gray-400 bg-surface-light hover:text-white"
            }`}
            style={mode === m.mode ? { backgroundColor: m.accent } : undefined}
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* Main layout */}
      <div className="flex-1 flex gap-6 min-h-0 overflow-hidden">
        {/* Left: Controls */}
        <div className="flex-1 space-y-4 overflow-y-auto pr-2">
          {/* Colors */}
          <div className="p-4 rounded-xl border border-surface-border bg-surface-light space-y-3">
            <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Colors</h3>
            <ColorPicker
              label="Accent"
              value={profile.colors.accent}
              onChange={(v) => update("colors.accent", v)}
              presets={ACCENT_PRESETS}
            />
            <ColorPicker
              label="Light"
              value={profile.colors.accentLight}
              onChange={(v) => update("colors.accentLight", v)}
            />
            <ColorPicker
              label="Dark"
              value={profile.colors.accentDark}
              onChange={(v) => update("colors.accentDark", v)}
            />
            <ColorPicker
              label="Background"
              value={profile.colors.bg}
              onChange={(v) => update("colors.bg", v)}
            />
            <ColorPicker
              label="Text"
              value={profile.colors.text}
              onChange={(v) => update("colors.text", v)}
            />
            <ColorPicker
              label="Text Soft"
              value={profile.colors.textSoft}
              onChange={(v) => update("colors.textSoft", v)}
            />
            <ColorPicker
              label="Term BG"
              value={profile.colors.termBg}
              onChange={(v) => update("colors.termBg", v)}
            />
            <ColorPicker
              label="Term Border"
              value={profile.colors.termBorder}
              onChange={(v) => update("colors.termBorder", v)}
            />
          </div>

          {/* Fonts */}
          <div className="p-4 rounded-xl border border-surface-border bg-surface-light space-y-3">
            <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Fonts</h3>
            <FontSelector
              label="Heading"
              value={profile.fonts.heading}
              onChange={(v) => update("fonts.heading", v)}
            />
            <FontSelector
              label="Body"
              value={profile.fonts.body}
              onChange={(v) => update("fonts.body", v)}
            />
            <FontSelector
              label="Mono"
              value={profile.fonts.mono}
              onChange={(v) => update("fonts.mono", v)}
            />
          </div>

          {/* Captions */}
          <div className="p-4 rounded-xl border border-surface-border bg-surface-light space-y-3">
            <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Captions</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <label className="text-xs text-gray-400 w-20 shrink-0">Size</label>
                <input
                  type="range"
                  min={40}
                  max={100}
                  value={profile.captions.fontSize}
                  onChange={(e) => update("captions.fontSize", parseInt(e.target.value))}
                  className="flex-1"
                  style={{ accentColor: accent }}
                />
                <span className="text-xs font-mono w-8 text-right" style={{ color: accent }}>
                  {profile.captions.fontSize}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <label className="text-xs text-gray-400 w-20 shrink-0">Active</label>
                <input
                  type="range"
                  min={50}
                  max={120}
                  value={profile.captions.activeFontSize}
                  onChange={(e) => update("captions.activeFontSize", parseInt(e.target.value))}
                  className="flex-1"
                  style={{ accentColor: accent }}
                />
                <span className="text-xs font-mono w-8 text-right" style={{ color: accent }}>
                  {profile.captions.activeFontSize}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <label className="text-xs text-gray-400 w-20 shrink-0">Top</label>
                <input
                  type="range"
                  min={1200}
                  max={1700}
                  value={profile.captions.top}
                  onChange={(e) => update("captions.top", parseInt(e.target.value))}
                  className="flex-1"
                  style={{ accentColor: accent }}
                />
                <span className="text-xs font-mono w-12 text-right" style={{ color: accent }}>
                  {profile.captions.top}
                </span>
              </div>
            </div>
          </div>

          {/* Badge */}
          <div className="p-4 rounded-xl border border-surface-border bg-surface-light">
            <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Badge Text</h3>
            <input
              value={profile.badge}
              onChange={(e) => update("badge", e.target.value)}
              className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
            />
          </div>

          {/* Animation */}
          <div className="p-4 rounded-xl border border-surface-border bg-surface-light">
            <AnimationPicker
              value={profile.animation}
              onChange={(v) => update("animation", v)}
              accent={accent}
            />
          </div>
        </div>

        {/* Right: Live preview */}
        <div className="shrink-0 space-y-4">
          <BrandPreview profile={profile} />

          <div className="space-y-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="w-full py-2.5 rounded-lg text-sm font-bold transition-colors disabled:opacity-50"
              style={{ backgroundColor: accent, color: "#000" }}
            >
              {saving ? "Saving..." : "Save Brand Profile"}
            </button>
            <button
              onClick={() => loadBrand(mode)}
              className="w-full py-2 rounded-lg text-sm font-medium border border-surface-border text-gray-400 hover:text-white transition-colors"
            >
              Reset to Default
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
