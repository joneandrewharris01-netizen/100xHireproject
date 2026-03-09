"use client";

const ACCENT: Record<string, string> = {
  wealth: "#00D4FF",
  apps: "#22C55E",
  finance: "#D4A843",
  custom: "#8B5CF6",
};

interface OutputCardProps {
  filename: string;
  mode: string;
  videoUrl: string;
  sizeFormatted: string;
  createdAt: string;
}

export function OutputCard({ filename, mode, videoUrl, sizeFormatted, createdAt }: OutputCardProps) {
  const accent = ACCENT[mode] || ACCENT.custom;
  const date = new Date(createdAt).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className="rounded-xl border border-surface-border bg-surface-light overflow-hidden group">
      {/* Video player */}
      <div className="relative aspect-[9/16] max-h-80 bg-black">
        <video
          src={videoUrl}
          controls
          className="w-full h-full object-contain"
          preload="metadata"
        />
      </div>

      {/* Info */}
      <div className="p-3">
        <div className="flex items-center gap-2 mb-1">
          <span
            className="text-xs font-bold px-2 py-0.5 rounded-full"
            style={{ backgroundColor: `${accent}20`, color: accent }}
          >
            {mode}
          </span>
          <span className="text-xs text-gray-500">{sizeFormatted}</span>
        </div>
        <p className="text-xs text-gray-400 font-mono truncate">{filename}</p>
        <p className="text-xs text-gray-500 mt-1">{date}</p>

        {/* Download */}
        <a
          href={videoUrl}
          download={filename}
          className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-gray-400 hover:text-white transition-colors"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download
        </a>
      </div>
    </div>
  );
}
