"use client";

import { useState } from "react";
import type { SceneDef } from "../src/types/content";

interface ScriptPreviewProps {
  title: string;
  scenes: SceneDef[];
  cta: { line1: string; line2?: string; button?: string };
  voiceoverScript: string;
  onUpdate: (updates: {
    title?: string;
    scenes?: SceneDef[];
    cta?: { line1: string; line2?: string; button?: string };
    voiceoverScript?: string;
  }) => void;
  accent?: string;
}

export function ScriptPreview({
  title,
  scenes,
  cta,
  voiceoverScript,
  onUpdate,
  accent = "#00D4FF",
}: ScriptPreviewProps) {
  const [editingVoiceover, setEditingVoiceover] = useState(false);
  const [voText, setVoText] = useState(voiceoverScript);

  return (
    <div className="space-y-4">
      {/* Title */}
      <div>
        <label className="block text-xs text-gray-500 uppercase tracking-wider mb-1">Title</label>
        <input
          value={title}
          onChange={(e) => onUpdate({ title: e.target.value })}
          className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-gray-500"
        />
      </div>

      {/* Scenes */}
      <div>
        <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">
          Scenes ({scenes.length})
        </label>
        <div className="space-y-2">
          {scenes.map((scene, i) => (
            <div
              key={scene.id}
              className="p-3 rounded-lg border border-surface-border bg-surface-light"
            >
              <div className="flex items-center gap-2 mb-2">
                <span
                  className="text-xs px-2 py-0.5 rounded font-mono"
                  style={{ backgroundColor: `${accent}20`, color: accent }}
                >
                  {scene.id}
                </span>
                <input
                  value={scene.label}
                  onChange={(e) => {
                    const updated = [...scenes];
                    updated[i] = { ...updated[i], label: e.target.value };
                    onUpdate({ scenes: updated });
                  }}
                  className="flex-1 bg-transparent text-sm font-medium text-white focus:outline-none border-b border-transparent focus:border-gray-600"
                />
              </div>
              <textarea
                value={scene.text}
                onChange={(e) => {
                  const updated = [...scenes];
                  updated[i] = { ...updated[i], text: e.target.value };
                  onUpdate({ scenes: updated });
                }}
                rows={2}
                className="w-full bg-surface border border-surface-border rounded px-2 py-1.5 text-xs text-gray-300 focus:outline-none resize-none"
              />
              {scene.data && Object.keys(scene.data).length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {Object.entries(scene.data).map(([k, v]) => (
                    <span key={k} className="text-xs px-2 py-0.5 rounded bg-surface-lighter text-gray-400">
                      {k}: <span className="text-white">{String(v)}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div>
        <label className="block text-xs text-gray-500 uppercase tracking-wider mb-1">CTA</label>
        <div className="grid grid-cols-3 gap-2">
          <input
            value={cta.line1}
            onChange={(e) => onUpdate({ cta: { ...cta, line1: e.target.value } })}
            placeholder="Line 1"
            className="bg-surface border border-surface-border rounded px-2 py-1.5 text-xs text-white focus:outline-none"
          />
          <input
            value={cta.line2 || ""}
            onChange={(e) => onUpdate({ cta: { ...cta, line2: e.target.value } })}
            placeholder="Line 2"
            className="bg-surface border border-surface-border rounded px-2 py-1.5 text-xs text-white focus:outline-none"
          />
          <input
            value={cta.button || ""}
            onChange={(e) => onUpdate({ cta: { ...cta, button: e.target.value } })}
            placeholder="Button"
            className="bg-surface border border-surface-border rounded px-2 py-1.5 text-xs text-white focus:outline-none"
          />
        </div>
      </div>

      {/* Voiceover */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="block text-xs text-gray-500 uppercase tracking-wider">
            Voiceover Script
          </label>
          <button
            onClick={() => {
              if (editingVoiceover) {
                onUpdate({ voiceoverScript: voText });
              }
              setEditingVoiceover(!editingVoiceover);
            }}
            className="text-xs hover:text-white transition-colors"
            style={{ color: accent }}
          >
            {editingVoiceover ? "Save" : "Edit"}
          </button>
        </div>
        {editingVoiceover ? (
          <textarea
            value={voText}
            onChange={(e) => setVoText(e.target.value)}
            rows={4}
            className="w-full bg-surface border border-surface-border rounded-lg p-3 text-sm text-white focus:outline-none resize-none"
          />
        ) : (
          <div className="p-3 rounded-lg bg-surface-light border border-surface-border text-sm text-gray-300 leading-relaxed">
            {voiceoverScript}
          </div>
        )}
        <p className="text-xs text-gray-600 mt-1">
          {voiceoverScript.split(/\s+/).length} words (~{Math.round(voiceoverScript.split(/\s+/).length / 2.5)}s)
        </p>
      </div>
    </div>
  );
}
