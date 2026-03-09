"use client";

import { Suspense, useEffect, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ScriptList } from "../../components/ScriptList";

const MODES = [
  { mode: "wealth", label: "Wealth", accent: "#00D4FF" },
  { mode: "apps", label: "Apps", accent: "#22C55E" },
  { mode: "finance", label: "Finance", accent: "#D4A843" },
  { mode: "custom", label: "Custom", accent: "#8B5CF6" },
];

interface ScriptItem {
  filename: string;
  id: string;
  title: string;
  hook: string;
  sceneCount: number;
  mode: string;
}

function ContentBrowserInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const activeMode = searchParams.get("mode") || "wealth";
  const [scripts, setScripts] = useState<ScriptItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectingFile, setSelectingFile] = useState<string | null>(null);

  const fetchScripts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/scripts?mode=${activeMode}`);
      const data = await res.json();
      setScripts(data.scripts || []);
    } catch {
      setScripts([]);
    }
    setLoading(false);
  }, [activeMode]);

  useEffect(() => {
    fetchScripts();
  }, [fetchScripts]);

  async function handleSelect(filename: string) {
    setSelectingFile(filename);
    try {
      await fetch("/api/pick", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode: activeMode,
          file: `content/${activeMode}/${filename}`,
        }),
      });
      alert(`Loaded ${filename} into today.json`);
    } catch {
      alert("Failed to load script");
    }
    setSelectingFile(null);
  }

  async function handleDelete(filename: string) {
    try {
      await fetch(`/api/scripts?mode=${activeMode}&file=${encodeURIComponent(filename)}`, {
        method: "DELETE",
      });
      fetchScripts();
    } catch {
      alert("Failed to delete script");
    }
  }

  const accent = MODES.find((m) => m.mode === activeMode)?.accent || "#666";

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold mb-1">Content Browser</h2>
          <p className="text-gray-400 text-sm">Browse and manage content scripts per mode.</p>
        </div>
        <button
          onClick={() => router.push(`/editor?mode=${activeMode}`)}
          className="px-4 py-2 rounded-lg text-sm font-bold transition-colors"
          style={{ backgroundColor: accent, color: "#000" }}
        >
          + New Script
        </button>
      </div>

      {/* Mode tabs */}
      <div className="flex gap-1 mb-6 p-1 bg-surface-light rounded-lg border border-surface-border w-fit">
        {MODES.map((m) => (
          <button
            key={m.mode}
            onClick={() => router.push(`/content?mode=${m.mode}`)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeMode === m.mode
                ? "text-white"
                : "text-gray-400 hover:text-white hover:bg-surface-lighter/50"
            }`}
            style={
              activeMode === m.mode
                ? { backgroundColor: `${m.accent}20`, color: m.accent }
                : undefined
            }
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* Script list */}
      {loading ? (
        <div className="py-12 text-center text-gray-500">Loading scripts...</div>
      ) : (
        <ScriptList
          scripts={scripts}
          mode={activeMode}
          onSelect={handleSelect}
          onDelete={handleDelete}
        />
      )}

      {selectingFile && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-surface-light p-6 rounded-xl border border-surface-border">
            <p className="text-sm">Loading {selectingFile}...</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ContentBrowser() {
  return (
    <Suspense fallback={<div className="py-12 text-center text-gray-500">Loading...</div>}>
      <ContentBrowserInner />
    </Suspense>
  );
}
