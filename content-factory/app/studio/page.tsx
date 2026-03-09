"use client";

import { useState } from "react";
import { PromptInput } from "../../components/PromptInput";
import { HookSelector } from "../../components/HookSelector";
import { ScriptPreview } from "../../components/ScriptPreview";

type ContentMode = "wealth" | "apps" | "finance" | "custom";

interface SceneDef {
  id: string;
  label: string;
  text: string;
  icon?: string;
  data?: Record<string, string | number>;
}

const MODES: { mode: ContentMode; label: string; accent: string }[] = [
  { mode: "wealth", label: "Wealth", accent: "#00D4FF" },
  { mode: "apps", label: "Apps", accent: "#22C55E" },
  { mode: "finance", label: "Finance", accent: "#D4A843" },
  { mode: "custom", label: "Custom", accent: "#8B5CF6" },
];

export default function StudioPage() {
  const [mode, setMode] = useState<ContentMode>("wealth");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Generated script state
  const [title, setTitle] = useState("");
  const [hooks, setHooks] = useState<string[]>([]);
  const [selectedHook, setSelectedHook] = useState(0);
  const [scenes, setScenes] = useState<SceneDef[]>([]);
  const [cta, setCta] = useState<{ line1: string; line2?: string; button?: string }>({
    line1: "",
  });
  const [voiceoverScript, setVoiceoverScript] = useState("");
  const [generated, setGenerated] = useState(false);
  const [saving, setSaving] = useState(false);

  const accent = MODES.find((m) => m.mode === mode)?.accent || "#00D4FF";

  async function handleGenerate(prompt: string, tone: string) {
    setLoading(true);
    setError("");
    setGenerated(false);

    try {
      const res = await fetch("/api/ai/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, mode, tone: tone || undefined, hooks: 3 }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Generation failed");
      }

      setTitle(data.title);
      setHooks(data.hooks);
      setSelectedHook(0);
      setScenes(data.scenes);
      setCta(data.cta);
      setVoiceoverScript(data.voiceoverScript);
      setGenerated(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Generation failed");
    }
    setLoading(false);
  }

  async function handleSave(andLoad: boolean = false) {
    setSaving(true);
    try {
      const scriptId = `${mode}-${Date.now()}`;
      const script = {
        id: scriptId,
        mode,
        title,
        hook: hooks[selectedHook],
        voiceoverScript,
        scenes,
        cta,
      };

      // Save to content/{mode}/
      const res = await fetch("/api/scripts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, script }),
      });

      if (!res.ok) throw new Error("Save failed");

      if (andLoad) {
        // Pick this script into today.json
        await fetch("/api/pick", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scriptId, mode }),
        });
        window.location.href = "/audio";
      } else {
        alert("Script saved!");
      }
    } catch {
      alert("Failed to save script");
    }
    setSaving(false);
  }

  return (
    <div className="h-[calc(100vh-3rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold mb-1">AI Script Studio</h2>
          <p className="text-gray-400 text-sm">
            Generate scripts with AI — pick hooks, edit scenes, save & render.
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

      {/* Main content */}
      <div className="flex-1 overflow-y-auto space-y-6">
        {/* Prompt input */}
        <div className="p-4 rounded-xl border border-surface-border bg-surface-light">
          <PromptInput mode={mode} onGenerate={handleGenerate} loading={loading} />
        </div>

        {/* Error */}
        {error && (
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Generated content */}
        {generated && (
          <>
            {/* Hook selector */}
            <div className="p-4 rounded-xl border border-surface-border bg-surface-light">
              <HookSelector
                hooks={hooks}
                selected={selectedHook}
                onSelect={setSelectedHook}
                accent={accent}
              />
            </div>

            {/* Script preview / editor */}
            <div className="p-4 rounded-xl border border-surface-border bg-surface-light">
              <ScriptPreview
                title={title}
                scenes={scenes}
                cta={cta}
                voiceoverScript={voiceoverScript}
                accent={accent}
                onUpdate={(updates) => {
                  if (updates.title !== undefined) setTitle(updates.title);
                  if (updates.scenes) setScenes(updates.scenes);
                  if (updates.cta) setCta(updates.cta);
                  if (updates.voiceoverScript !== undefined)
                    setVoiceoverScript(updates.voiceoverScript);
                }}
              />
            </div>

            {/* Action buttons */}
            <div className="flex gap-3 pb-6">
              <button
                onClick={() => handleSave(false)}
                disabled={saving}
                className="px-6 py-2.5 rounded-lg text-sm font-medium border border-surface-border bg-surface-light text-white hover:bg-surface-lighter transition-colors disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Script"}
              </button>
              <button
                onClick={() => handleSave(true)}
                disabled={saving}
                className="px-6 py-2.5 rounded-lg text-sm font-bold transition-colors disabled:opacity-50"
                style={{ backgroundColor: accent, color: "#000" }}
              >
                {saving ? "Saving..." : "Save & Open Audio Studio"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
