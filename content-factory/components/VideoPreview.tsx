"use client";

import { useEffect, useState } from "react";

// Dynamic import to avoid SSR issues with Remotion Player
import dynamic from "next/dynamic";

const PlayerComponent = dynamic(
  () => import("./RemotionPlayerWrapper"),
  { ssr: false, loading: () => <div className="flex items-center justify-center h-full text-gray-500">Loading player...</div> }
);

interface VideoPreviewProps {
  mode: string;
  data: Record<string, unknown> | null;
}

export function VideoPreview({ mode, data }: VideoPreviewProps) {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <p>No content loaded. Pick a script first.</p>
      </div>
    );
  }

  return <PlayerComponent mode={mode} data={data} />;
}
