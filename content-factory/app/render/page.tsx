"use client";

import { useState } from "react";
import { RenderPanel } from "../../components/RenderPanel";

const MODES = [
  { mode: "wealth", label: "Wealth", accent: "#00D4FF" },
  { mode: "apps", label: "Apps", accent: "#22C55E" },
  { mode: "finance", label: "Finance", accent: "#D4A843" },
  { mode: "custom", label: "Custom", accent: "#8B5CF6" },
];

export default function RenderPage() {
  const [selectedMode, setSelectedMode] = useState("wealth");
  const accent = MODES.find((m) => m.mode === selectedMode)?.accent || "#00D4FF";

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold mb-1">Render Pipeline</h2>
          <p className="text-gray-400 text-sm">
            Full pipeline: Pick Content → Generate Audio → Render Video
          </p>
        </div>
      </div>

      {/* Mode selector */}
      <div className="flex gap-1 mb-6 p-1 bg-surface-light rounded-lg border border-surface-border w-fit">
        {MODES.map((m) => (
          <button
            key={m.mode}
            onClick={() => setSelectedMode(m.mode)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedMode === m.mode
                ? "text-white"
                : "text-gray-400 hover:text-white hover:bg-surface-lighter/50"
            }`}
            style={
              selectedMode === m.mode
                ? { backgroundColor: `${m.accent}20`, color: m.accent }
                : undefined
            }
          >
            {m.label}
          </button>
        ))}
      </div>

      <div className="max-w-2xl">
        <RenderPanel mode={selectedMode} />
      </div>
    </div>
  );
}
