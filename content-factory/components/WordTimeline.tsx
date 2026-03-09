"use client";

import { useRef, useEffect } from "react";

interface WordTimelineProps {
  words: { word: string; start: number; end: number }[];
  currentTime: number;
  accent?: string;
}

export function WordTimeline({ words, currentTime, accent = "#00D4FF" }: WordTimelineProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to current word
  useEffect(() => {
    if (!containerRef.current) return;
    const activeWord = containerRef.current.querySelector("[data-active='true']");
    if (activeWord) {
      activeWord.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
    }
  }, [currentTime]);

  if (!words.length) {
    return (
      <div className="rounded-lg border border-surface-border bg-surface-light p-4">
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Word Timeline</p>
        <p className="text-sm text-gray-500">No word timestamps available</p>
      </div>
    );
  }

  return (
    <div>
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Word Timeline</p>
      <div
        ref={containerRef}
        className="rounded-lg border border-surface-border bg-surface-light p-3 overflow-x-auto"
      >
        <div className="flex flex-wrap gap-1">
          {words.map((w, i) => {
            const isActive = currentTime >= w.start && currentTime < w.end;
            return (
              <span
                key={i}
                data-active={isActive}
                className="inline-flex flex-col items-center px-1.5 py-1 rounded text-xs transition-all"
                style={
                  isActive
                    ? { backgroundColor: `${accent}20`, color: accent, fontWeight: 700 }
                    : { color: "#888" }
                }
              >
                <span>{w.word}</span>
                <span className="text-[10px] opacity-50 font-mono">{w.start.toFixed(1)}s</span>
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}
