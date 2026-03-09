"use client";

import { Player } from "@remotion/player";
import { useMemo } from "react";

// Import compositions
import { WealthVideo } from "../src/compositions/WealthVideo";
import { AppsVideo } from "../src/compositions/AppsVideo";
import { FinanceVideo } from "../src/compositions/FinanceVideo";
import { CustomVideo } from "../src/compositions/CustomVideo";
import { getTotalFrames } from "../src/utils/timing";
import type { ContentData } from "../src/types/content";

const COMPOSITION_MAP: Record<string, React.FC<{ data: ContentData }>> = {
  wealth: WealthVideo,
  apps: AppsVideo,
  finance: FinanceVideo,
  custom: CustomVideo,
};

interface Props {
  mode: string;
  data: Record<string, unknown>;
}

export default function RemotionPlayerWrapper({ mode, data }: Props) {
  const typedData = data as unknown as ContentData;
  const Component = COMPOSITION_MAP[mode] || COMPOSITION_MAP.wealth;
  const durationSeconds = typedData?.audio?.durationSeconds || 25;
  const durationInFrames = useMemo(() => getTotalFrames(durationSeconds), [durationSeconds]);

  return (
    <div className="flex items-center justify-center h-full">
      <Player
        component={Component as React.ComponentType<Record<string, unknown>>}
        durationInFrames={durationInFrames}
        fps={30}
        compositionWidth={1080}
        compositionHeight={1920}
        inputProps={{ data: typedData }}
        style={{ width: 360, height: 640, borderRadius: 12 }}
        controls
        autoPlay={false}
      />
    </div>
  );
}
