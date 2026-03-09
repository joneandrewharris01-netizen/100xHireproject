"use client";

import { useEffect, useState } from "react";
import { OutputCard } from "../../components/OutputCard";

const MODES = [
  { mode: "all", label: "All" },
  { mode: "wealth", label: "Wealth", accent: "#00D4FF" },
  { mode: "apps", label: "Apps", accent: "#22C55E" },
  { mode: "finance", label: "Finance", accent: "#D4A843" },
  { mode: "custom", label: "Custom", accent: "#8B5CF6" },
];

interface OutputItem {
  filename: string;
  mode: string;
  path: string;
  size: number;
  sizeFormatted: string;
  createdAt: string;
}

export default function GalleryPage() {
  const [outputs, setOutputs] = useState<OutputItem[]>([]);
  const [filterMode, setFilterMode] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchOutputs() {
      setLoading(true);
      try {
        const url = filterMode === "all" ? "/api/outputs" : `/api/outputs?mode=${filterMode}`;
        const res = await fetch(url);
        const data = await res.json();
        setOutputs(data.outputs || []);
      } catch {
        setOutputs([]);
      }
      setLoading(false);
    }
    fetchOutputs();
  }, [filterMode]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold mb-1">Gallery</h2>
          <p className="text-gray-400 text-sm">
            Browse rendered videos. {outputs.length} video{outputs.length !== 1 ? "s" : ""} found.
          </p>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 mb-6 p-1 bg-surface-light rounded-lg border border-surface-border w-fit">
        {MODES.map((m) => (
          <button
            key={m.mode}
            onClick={() => setFilterMode(m.mode)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              filterMode === m.mode
                ? "bg-surface-lighter text-white"
                : "text-gray-400 hover:text-white hover:bg-surface-lighter/50"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* Output grid */}
      {loading ? (
        <div className="py-12 text-center text-gray-500">Loading outputs...</div>
      ) : outputs.length === 0 ? (
        <div className="py-12 text-center text-gray-500">
          <p className="text-lg mb-2">No videos rendered yet</p>
          <p className="text-sm">Go to the Render page to generate your first video.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {outputs.map((output) => (
            <OutputCard
              key={`${output.mode}/${output.filename}`}
              filename={output.filename}
              mode={output.mode}
              videoUrl={output.path}
              sizeFormatted={output.sizeFormatted}
              createdAt={output.createdAt}
            />
          ))}
        </div>
      )}
    </div>
  );
}
