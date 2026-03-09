"use client";

interface HookSelectorProps {
  hooks: string[];
  selected: number;
  onSelect: (index: number) => void;
  accent?: string;
}

export function HookSelector({ hooks, selected, onSelect, accent = "#00D4FF" }: HookSelectorProps) {
  if (!hooks.length) return null;

  return (
    <div className="space-y-2">
      <label className="block text-xs text-gray-500 uppercase tracking-wider">
        Choose a hook ({hooks.length} options)
      </label>
      <div className="grid gap-2">
        {hooks.map((hook, i) => {
          const isActive = i === selected;
          return (
            <button
              key={i}
              onClick={() => onSelect(i)}
              className={`text-left p-3 rounded-lg border transition-all text-sm ${
                isActive
                  ? "border-opacity-60 bg-opacity-10"
                  : "border-surface-border bg-surface-light hover:bg-surface-lighter"
              }`}
              style={
                isActive
                  ? {
                      borderColor: accent,
                      backgroundColor: `${accent}15`,
                      boxShadow: `0 0 12px ${accent}20`,
                    }
                  : undefined
              }
            >
              <div className="flex items-start gap-2">
                <span
                  className="shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mt-0.5"
                  style={
                    isActive
                      ? { backgroundColor: accent, color: "#000" }
                      : { backgroundColor: "#1A2035", color: "#666" }
                  }
                >
                  {i + 1}
                </span>
                <span className={isActive ? "text-white" : "text-gray-400"}>
                  "{hook}"
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
