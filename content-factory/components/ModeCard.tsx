"use client";

import { useRouter } from "next/navigation";

interface ModeCardProps {
  mode: string;
  label: string;
  accent: string;
  description: string;
  scriptCount: number;
  compositionId: string;
}

export function ModeCard({ mode, label, accent, description, scriptCount, compositionId }: ModeCardProps) {
  const router = useRouter();

  return (
    <button
      onClick={() => router.push(`/content?mode=${mode}`)}
      className="group relative p-6 rounded-xl border border-surface-border bg-surface-light hover:bg-surface-lighter transition-all text-left w-full"
      style={{ borderColor: `${accent}20` }}
    >
      {/* Accent glow */}
      <div
        className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity"
        style={{ boxShadow: `inset 0 0 30px ${accent}10, 0 0 20px ${accent}08` }}
      />

      <div className="relative z-10">
        {/* Mode badge */}
        <div
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold mb-4"
          style={{ backgroundColor: `${accent}15`, color: accent }}
        >
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: accent }} />
          {label.toUpperCase()}
        </div>

        {/* Title */}
        <h3 className="text-xl font-bold mb-2 text-white group-hover:text-white/90">
          {label} Mode
        </h3>

        {/* Description */}
        <p className="text-sm text-gray-400 mb-4 leading-relaxed">
          {description}
        </p>

        {/* Stats */}
        <div className="flex gap-4 text-xs text-gray-500">
          <span>
            <strong className="text-gray-300">{scriptCount}</strong> scripts
          </span>
          <span>
            Comp: <strong className="text-gray-300 font-mono">{compositionId}</strong>
          </span>
        </div>
      </div>
    </button>
  );
}
