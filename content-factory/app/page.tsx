"use client";

import { useEffect, useState } from "react";
import { ModeCard } from "../components/ModeCard";

const MODES = [
  {
    mode: "wealth",
    label: "Wealth",
    accent: "#00D4FF",
    description: "Hacker terminal aesthetic. Automation case studies, client savings, DM funnels.",
    compositionId: "WealthVideo",
  },
  {
    mode: "apps",
    label: "Apps",
    accent: "#22C55E",
    description: "Code editor aesthetic. App ideas, revenue reveals, speed builds, research data.",
    compositionId: "AppsVideo",
  },
  {
    mode: "finance",
    label: "Finance",
    accent: "#D4A843",
    description: "Bloomberg aesthetic. Tax strategies, financial data, geographic insights, AI analysis.",
    compositionId: "FinanceVideo",
  },
  {
    mode: "custom",
    label: "Custom",
    accent: "#8B5CF6",
    description: "Fully overrideable theme. Dynamic N-scene template for testing new formats.",
    compositionId: "CustomVideo",
  },
];

interface ModeStats {
  mode: string;
  scriptCount: number;
}

export default function DashboardHome() {
  const [stats, setStats] = useState<ModeStats[]>([]);
  const [todayTitle, setTodayTitle] = useState<string>("");
  const [todayMode, setTodayMode] = useState<string>("");

  useEffect(() => {
    // Fetch script counts per mode
    Promise.all(
      MODES.map((m) =>
        fetch(`/api/scripts?mode=${m.mode}`)
          .then((r) => r.json())
          .then((d) => ({ mode: m.mode, scriptCount: d.scripts?.length || 0 }))
          .catch(() => ({ mode: m.mode, scriptCount: 0 }))
      )
    ).then(setStats);

    // Fetch current today.json
    fetch("/api/today")
      .then((r) => r.json())
      .then((d) => {
        if (d.script) {
          setTodayTitle(d.script.title || "");
          setTodayMode(d.script.mode || "");
        }
      })
      .catch(() => {});
  }, []);

  function getScriptCount(mode: string) {
    return stats.find((s) => s.mode === mode)?.scriptCount || 0;
  }

  const totalScripts = stats.reduce((sum, s) => sum + s.scriptCount, 0);

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-1">Content Factory</h2>
        <p className="text-gray-400 text-sm">
          Multi-mode video pipeline. Pick a mode to get started.
        </p>
      </div>

      {/* Quick stats bar */}
      <div className="flex gap-6 mb-8 p-4 rounded-lg bg-surface-light border border-surface-border">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider">Total Scripts</p>
          <p className="text-xl font-bold">{totalScripts}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider">Modes</p>
          <p className="text-xl font-bold">4</p>
        </div>
        {todayTitle && (
          <div className="border-l border-surface-border pl-6">
            <p className="text-xs text-gray-500 uppercase tracking-wider">Currently Loaded</p>
            <p className="text-sm font-medium mt-0.5">
              <span
                className="font-mono text-xs px-1.5 py-0.5 rounded mr-2"
                style={{
                  backgroundColor: `${MODES.find((m) => m.mode === todayMode)?.accent || "#666"}20`,
                  color: MODES.find((m) => m.mode === todayMode)?.accent || "#666",
                }}
              >
                {todayMode}
              </span>
              {todayTitle}
            </p>
          </div>
        )}
      </div>

      {/* Mode cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {MODES.map((m) => (
          <ModeCard
            key={m.mode}
            mode={m.mode}
            label={m.label}
            accent={m.accent}
            description={m.description}
            scriptCount={getScriptCount(m.mode)}
            compositionId={m.compositionId}
          />
        ))}
      </div>
    </div>
  );
}
