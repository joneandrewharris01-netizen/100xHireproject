"use client";

import { useRouter } from "next/navigation";

interface ScriptItem {
  filename: string;
  id: string;
  title: string;
  hook: string;
  sceneCount: number;
  mode: string;
}

interface ScriptListProps {
  scripts: ScriptItem[];
  mode: string;
  onSelect: (filename: string) => void;
  onDelete: (filename: string) => void;
}

const ACCENT: Record<string, string> = {
  wealth: "#00D4FF",
  apps: "#22C55E",
  finance: "#D4A843",
  custom: "#8B5CF6",
};

export function ScriptList({ scripts, mode, onSelect, onDelete }: ScriptListProps) {
  const router = useRouter();
  const accent = ACCENT[mode] || ACCENT.custom;

  if (scripts.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg mb-2">No scripts found</p>
        <p className="text-sm">Create one in the Editor</p>
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      {scripts.map((script) => (
        <div
          key={script.filename}
          className="group p-4 rounded-lg border border-surface-border bg-surface-light hover:bg-surface-lighter transition-all"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <h4 className="font-semibold text-white truncate">{script.title}</h4>
              <p className="text-sm text-gray-400 mt-1 line-clamp-2">{script.hook}</p>
              <div className="flex gap-3 mt-2 text-xs text-gray-500">
                <span className="font-mono">{script.filename}</span>
                <span>{script.sceneCount} scenes</span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
              <button
                onClick={() => onSelect(script.filename)}
                className="px-3 py-1.5 text-xs rounded-md font-medium transition-colors"
                style={{ backgroundColor: `${accent}20`, color: accent }}
                title="Load into today.json"
              >
                Select
              </button>
              <button
                onClick={() =>
                  router.push(`/editor?mode=${mode}&file=${encodeURIComponent(script.filename)}`)
                }
                className="px-3 py-1.5 text-xs rounded-md bg-surface-lighter text-gray-300 hover:text-white transition-colors"
              >
                Edit
              </button>
              <button
                onClick={() => {
                  if (confirm(`Delete ${script.filename}?`)) {
                    onDelete(script.filename);
                  }
                }}
                className="px-3 py-1.5 text-xs rounded-md bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
