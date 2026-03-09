"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ScriptEditor } from "../../components/ScriptEditor";

const ACCENT: Record<string, string> = {
  wealth: "#00D4FF",
  apps: "#22C55E",
  finance: "#D4A843",
  custom: "#8B5CF6",
};

function EditorPageInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const mode = searchParams.get("mode") || "wealth";
  const file = searchParams.get("file") || "";
  const [initialData, setInitialData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(!!file);

  useEffect(() => {
    if (!file) {
      setInitialData(null);
      setLoading(false);
      return;
    }

    fetch(`/api/script-file?mode=${mode}&file=${encodeURIComponent(file)}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((content) => {
        if (content) setInitialData(content);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [mode, file]);

  async function handleSave(data: Record<string, unknown>) {
    const filename = file || `${(data.id as string) || "new-script"}.json`;
    try {
      const res = await fetch("/api/scripts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, filename, content: data }),
      });
      if (res.ok) {
        if (!file) {
          router.replace(`/editor?mode=${mode}&file=${encodeURIComponent(filename)}`);
        }
      } else {
        alert("Save failed");
      }
    } catch {
      alert("Save failed");
    }
  }

  async function handleLoadToPipeline() {
    if (!file) {
      alert("Save the script first before loading it into the pipeline.");
      return;
    }
    try {
      await fetch("/api/pick", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, file: `content/${mode}/${file}` }),
      });
      alert("Loaded into today.json! Go to Preview to see it.");
    } catch {
      alert("Failed to load into pipeline");
    }
  }

  if (loading) {
    return <div className="py-12 text-center text-gray-500">Loading script...</div>;
  }

  const accent = ACCENT[mode] || ACCENT.custom;

  return (
    <div className="h-[calc(100vh-3rem)] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold mb-1">Script Editor</h2>
          <p className="text-gray-400 text-sm">
            {file ? `Editing ${file}` : "Create a new script"}{" "}
            <span className="font-mono" style={{ color: accent }}>
              [{mode}]
            </span>
          </p>
        </div>
        <button
          onClick={handleLoadToPipeline}
          className="px-4 py-2 rounded-lg text-sm font-medium bg-surface-lighter text-gray-300 hover:text-white border border-surface-border transition-colors"
        >
          Load to Pipeline
        </button>
      </div>

      <div className="flex-1 min-h-0">
        <ScriptEditor
          initialData={initialData}
          mode={mode}
          filename={file}
          onSave={handleSave}
        />
      </div>
    </div>
  );
}

export default function EditorPage() {
  return (
    <Suspense fallback={<div className="py-12 text-center text-gray-500">Loading...</div>}>
      <EditorPageInner />
    </Suspense>
  );
}
