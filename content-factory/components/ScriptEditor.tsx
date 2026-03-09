"use client";

import { useState } from "react";

interface ScriptEditorProps {
  initialData: Record<string, unknown> | null;
  mode: string;
  filename: string;
  onSave: (data: Record<string, unknown>) => void;
}

const ACCENT: Record<string, string> = {
  wealth: "#00D4FF",
  apps: "#22C55E",
  finance: "#D4A843",
  custom: "#8B5CF6",
};

function getBlankScript(mode: string): Record<string, unknown> {
  return {
    id: `${mode}-new`,
    mode,
    title: "",
    hook: "",
    voiceoverScript: "",
    scenes: [
      { id: "scene-1", label: "", text: "", data: {} },
    ],
    cta: { line1: "DM me", line2: "AUTOMATE", button: "Follow + DM" },
  };
}

export function ScriptEditor({ initialData, mode, filename, onSave }: ScriptEditorProps) {
  const [viewMode, setViewMode] = useState<"form" | "json">("form");
  const [data, setData] = useState<Record<string, unknown>>(
    initialData || getBlankScript(mode)
  );
  const [jsonText, setJsonText] = useState(JSON.stringify(data, null, 2));
  const [saving, setSaving] = useState(false);

  const accent = ACCENT[mode] || ACCENT.custom;

  // Sync between form and JSON views
  function switchToJson() {
    setJsonText(JSON.stringify(data, null, 2));
    setViewMode("json");
  }

  function switchToForm() {
    try {
      const parsed = JSON.parse(jsonText);
      setData(parsed);
      setViewMode("form");
    } catch {
      alert("Invalid JSON — fix errors before switching to form view.");
    }
  }

  function updateField(path: string, value: unknown) {
    setData((prev) => {
      const clone = JSON.parse(JSON.stringify(prev));
      const keys = path.split(".");
      let obj = clone;
      for (let i = 0; i < keys.length - 1; i++) {
        obj = obj[keys[i]];
      }
      obj[keys[keys.length - 1]] = value;
      return clone;
    });
  }

  function handleSave() {
    const toSave = viewMode === "json" ? JSON.parse(jsonText) : data;
    setSaving(true);
    onSave(toSave);
    setTimeout(() => setSaving(false), 500);
  }

  const scenes = (data.scenes as Array<{ id: string; label: string; text: string; data: Record<string, unknown> }>) || [];
  const cta = (data.cta as { line1: string; line2?: string; button?: string }) || { line1: "" };

  function addScene() {
    const newScenes = [...scenes, { id: `scene-${scenes.length + 1}`, label: "", text: "", data: {} }];
    setData((prev) => ({ ...prev, scenes: newScenes }));
  }

  function removeScene(idx: number) {
    const newScenes = scenes.filter((_, i) => i !== idx);
    setData((prev) => ({ ...prev, scenes: newScenes }));
  }

  function moveScene(idx: number, dir: -1 | 1) {
    const newScenes = [...scenes];
    const target = idx + dir;
    if (target < 0 || target >= newScenes.length) return;
    [newScenes[idx], newScenes[target]] = [newScenes[target], newScenes[idx]];
    setData((prev) => ({ ...prev, scenes: newScenes }));
  }

  return (
    <div className="flex gap-6 h-full">
      {/* Toggle bar */}
      <div className="flex-1 flex flex-col">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex rounded-lg border border-surface-border overflow-hidden">
            <button
              onClick={viewMode === "json" ? switchToForm : undefined}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                viewMode === "form" ? "bg-surface-lighter text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              Form
            </button>
            <button
              onClick={viewMode === "form" ? switchToJson : undefined}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                viewMode === "json" ? "bg-surface-lighter text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              JSON
            </button>
          </div>

          <div className="flex-1" />

          <span className="text-xs text-gray-500 font-mono">{filename || "new-script.json"}</span>

          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 rounded-lg text-sm font-bold transition-colors"
            style={{ backgroundColor: accent, color: "#000" }}
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>

        {viewMode === "json" ? (
          <textarea
            value={jsonText}
            onChange={(e) => setJsonText(e.target.value)}
            className="json-editor flex-1 w-full bg-surface-light border border-surface-border rounded-lg p-4 text-white resize-none focus:outline-none focus:border-gray-600"
            spellCheck={false}
          />
        ) : (
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {/* Basic fields */}
            <FieldGroup label="Title">
              <input
                value={(data.title as string) || ""}
                onChange={(e) => updateField("title", e.target.value)}
                className="field-input"
                placeholder="Video title"
              />
            </FieldGroup>

            <FieldGroup label="Hook">
              <textarea
                value={(data.hook as string) || ""}
                onChange={(e) => updateField("hook", e.target.value)}
                className="field-input min-h-[60px]"
                placeholder="Opening hook text"
              />
            </FieldGroup>

            <FieldGroup label="Voiceover Script">
              <textarea
                value={(data.voiceoverScript as string) || ""}
                onChange={(e) => updateField("voiceoverScript", e.target.value)}
                className="field-input min-h-[120px]"
                placeholder="Full TTS script (25-45 seconds)"
              />
            </FieldGroup>

            {/* Scenes */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-300">Scenes ({scenes.length})</label>
                <button onClick={addScene} className="text-xs px-2 py-1 rounded bg-surface-lighter text-gray-300 hover:text-white">
                  + Add Scene
                </button>
              </div>
              <div className="space-y-3">
                {scenes.map((scene, idx) => (
                  <div key={idx} className="p-3 rounded-lg border border-surface-border bg-surface-light/50">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs text-gray-500 font-mono w-6">{idx + 1}</span>
                      <input
                        value={scene.id}
                        onChange={(e) => {
                          const newScenes = [...scenes];
                          newScenes[idx] = { ...newScenes[idx], id: e.target.value };
                          setData((prev) => ({ ...prev, scenes: newScenes }));
                        }}
                        className="field-input text-xs font-mono !py-1 w-24"
                        placeholder="id"
                      />
                      <input
                        value={scene.label}
                        onChange={(e) => {
                          const newScenes = [...scenes];
                          newScenes[idx] = { ...newScenes[idx], label: e.target.value };
                          setData((prev) => ({ ...prev, scenes: newScenes }));
                        }}
                        className="field-input !py-1 flex-1"
                        placeholder="Label"
                      />
                      <button onClick={() => moveScene(idx, -1)} className="text-gray-500 hover:text-white text-xs" title="Move up">^</button>
                      <button onClick={() => moveScene(idx, 1)} className="text-gray-500 hover:text-white text-xs" title="Move down">v</button>
                      <button onClick={() => removeScene(idx)} className="text-red-400 hover:text-red-300 text-xs">X</button>
                    </div>
                    <textarea
                      value={scene.text}
                      onChange={(e) => {
                        const newScenes = [...scenes];
                        newScenes[idx] = { ...newScenes[idx], text: e.target.value };
                        setData((prev) => ({ ...prev, scenes: newScenes }));
                      }}
                      className="field-input min-h-[50px] text-sm"
                      placeholder="Scene text"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* CTA */}
            <FieldGroup label="CTA">
              <div className="grid grid-cols-3 gap-2">
                <input
                  value={cta.line1 || ""}
                  onChange={(e) => updateField("cta.line1", e.target.value)}
                  className="field-input"
                  placeholder="Line 1"
                />
                <input
                  value={cta.line2 || ""}
                  onChange={(e) => updateField("cta.line2", e.target.value)}
                  className="field-input"
                  placeholder="Line 2"
                />
                <input
                  value={cta.button || ""}
                  onChange={(e) => updateField("cta.button", e.target.value)}
                  className="field-input"
                  placeholder="Button"
                />
              </div>
            </FieldGroup>
          </div>
        )}
      </div>
    </div>
  );
}

function FieldGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="text-sm font-medium text-gray-300 mb-1 block">{label}</label>
      {children}
    </div>
  );
}
