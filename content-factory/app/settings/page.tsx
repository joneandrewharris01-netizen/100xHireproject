"use client";

import { useEffect, useState } from "react";

const PROVIDERS = [
  { id: "gemini", label: "Gemini (Google)" },
  { id: "claude", label: "Claude (Anthropic)" },
  { id: "openai", label: "OpenAI (coming soon)", disabled: true },
];

const MODELS: Record<string, { id: string; label: string }[]> = {
  gemini: [
    { id: "gemini-2.0-flash", label: "Gemini 2.0 Flash (fast + free)" },
    { id: "gemini-2.0-flash-lite", label: "Gemini 2.0 Flash Lite (fastest)" },
    { id: "gemini-2.5-pro-preview-05-06", label: "Gemini 2.5 Pro (best quality)" },
  ],
  claude: [
    { id: "claude-sonnet-4-6", label: "Claude Sonnet 4.6 (fast + good)" },
    { id: "claude-opus-4-6", label: "Claude Opus 4.6 (best quality)" },
    { id: "claude-haiku-4-5", label: "Claude Haiku 4.5 (fastest)" },
  ],
  openai: [
    { id: "gpt-4o", label: "GPT-4o" },
  ],
};

const DEFAULT_MODELS: Record<string, string> = {
  gemini: "gemini-2.0-flash",
  claude: "claude-sonnet-4-6",
  openai: "gpt-4o",
};

const PLACEHOLDERS: Record<string, string> = {
  gemini: "AIzaSy...",
  claude: "sk-ant-api03-...",
  openai: "sk-...",
};

export default function SettingsPage() {
  const [provider, setProvider] = useState("gemini");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("gemini-2.0-flash");
  const [defaultVoice, setDefaultVoice] = useState("en-US-GuyNeural");
  const [defaultRate, setDefaultRate] = useState("+15%");
  const [defaultPitch, setDefaultPitch] = useState("+0Hz");

  const [hasKey, setHasKey] = useState(false);
  const [maskedKey, setMaskedKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null);
  const [showKey, setShowKey] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    try {
      const res = await fetch("/api/settings");
      if (res.ok) {
        const data = await res.json();
        setProvider(data.aiProvider || "gemini");
        setModel(data.model || DEFAULT_MODELS[data.aiProvider || "gemini"]);
        setDefaultVoice(data.defaultVoice || "en-US-GuyNeural");
        setDefaultRate(data.defaultRate || "+15%");
        setDefaultPitch(data.defaultPitch || "+0Hz");
        setHasKey(data.hasKey || false);
        setMaskedKey(data.apiKey || "");
      }
    } catch {
      // use defaults
    }
  }

  function handleProviderChange(newProvider: string) {
    setProvider(newProvider);
    setModel(DEFAULT_MODELS[newProvider] || "");
    setTestResult(null);
  }

  async function handleSave() {
    setSaving(true);
    setSaved(false);
    try {
      const body: Record<string, string> = {
        aiProvider: provider,
        model,
        defaultVoice,
        defaultRate,
        defaultPitch,
      };
      if (apiKey && !apiKey.includes("...")) {
        body.apiKey = apiKey;
      }

      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        const data = await res.json();
        setHasKey(data.hasKey);
        setMaskedKey(data.apiKey || "");
        setApiKey("");
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      }
    } catch {
      alert("Failed to save settings");
    }
    setSaving(false);
  }

  async function handleTestConnection() {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await fetch("/api/ai/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: "Say hello in one sentence.",
          mode: "wealth",
          hooks: 1,
        }),
      });
      const data = await res.json();
      if (res.ok && data.title) {
        setTestResult({ ok: true, message: `Connected! Generated: "${data.title}"` });
      } else {
        setTestResult({ ok: false, message: data.error || "Unknown error" });
      }
    } catch (err: unknown) {
      setTestResult({
        ok: false,
        message: err instanceof Error ? err.message : "Connection failed",
      });
    }
    setTesting(false);
  }

  const currentModels = MODELS[provider] || [];

  return (
    <div className="h-[calc(100vh-3rem)] flex flex-col">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-1">Settings</h2>
        <p className="text-gray-400 text-sm">
          Configure your AI provider, API key, and default preferences.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto max-w-2xl space-y-6">
        {/* AI Provider */}
        <div className="p-4 rounded-xl border border-surface-border bg-surface-light space-y-4">
          <h3 className="text-sm font-medium text-white">AI Provider</h3>

          <div>
            <label className="block text-xs text-gray-500 uppercase tracking-wider mb-1.5">
              Provider
            </label>
            <select
              value={provider}
              onChange={(e) => handleProviderChange(e.target.value)}
              className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
            >
              {PROVIDERS.map((p) => (
                <option key={p.id} value={p.id} disabled={p.disabled}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-500 uppercase tracking-wider mb-1.5">
              API Key
            </label>
            {hasKey && !apiKey && (
              <p className="text-xs text-green-400 mb-1.5">
                Key saved: {maskedKey}
              </p>
            )}
            <div className="flex gap-2">
              <input
                type={showKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={hasKey ? "Enter new key to replace..." : PLACEHOLDERS[provider] || "Enter API key..."}
                className="flex-1 bg-surface border border-surface-border rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none"
              />
              <button
                onClick={() => setShowKey(!showKey)}
                className="px-3 py-2 rounded-lg text-xs text-gray-400 border border-surface-border hover:text-white transition-colors"
              >
                {showKey ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs text-gray-500 uppercase tracking-wider mb-1.5">
              Model
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
            >
              {currentModels.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Default Voice Settings */}
        <div className="p-4 rounded-xl border border-surface-border bg-surface-light space-y-4">
          <h3 className="text-sm font-medium text-white">Default Audio Settings</h3>

          <div>
            <label className="block text-xs text-gray-500 uppercase tracking-wider mb-1.5">
              Default Voice
            </label>
            <input
              value={defaultVoice}
              onChange={(e) => setDefaultVoice(e.target.value)}
              placeholder="en-US-GuyNeural"
              className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 uppercase tracking-wider mb-1.5">
                Default Rate
              </label>
              <input
                value={defaultRate}
                onChange={(e) => setDefaultRate(e.target.value)}
                placeholder="+15%"
                className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 uppercase tracking-wider mb-1.5">
                Default Pitch
              </label>
              <input
                value={defaultPitch}
                onChange={(e) => setDefaultPitch(e.target.value)}
                placeholder="+0Hz"
                className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 items-center">
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-2.5 rounded-lg text-sm font-bold bg-wealth text-black transition-colors disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Settings"}
          </button>
          <button
            onClick={handleTestConnection}
            disabled={testing || !hasKey}
            className="px-4 py-2.5 rounded-lg text-sm font-medium border border-wealth text-wealth hover:bg-wealth/10 transition-colors disabled:opacity-50"
          >
            {testing ? "Testing..." : "Test Connection"}
          </button>
          {saved && (
            <span className="text-sm text-green-400">Saved!</span>
          )}
        </div>

        {testResult && (
          <div
            className={`p-3 rounded-lg text-sm ${
              testResult.ok
                ? "bg-green-500/10 border border-green-500/30 text-green-400"
                : "bg-red-500/10 border border-red-500/30 text-red-400"
            }`}
          >
            {testResult.message}
          </div>
        )}

        <div className="h-8" />
      </div>
    </div>
  );
}
