import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import type { ThemeConfig } from "../../types/themes";

export const ProgressBar: React.FC<{ theme: ThemeConfig }> = ({ theme }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const progress = interpolate(frame, [0, durationInFrames], [0, 100], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: 0,
        left: 0,
        right: 0,
        height: 6,
        background: theme.colors.surfaceAlpha50,
      }}
    >
      <div
        style={{
          height: "100%",
          width: `${progress}%`,
          background: `linear-gradient(90deg, ${theme.colors.accent}, ${theme.colors.accentLight})`,
          boxShadow: `0 0 12px ${theme.colors.accent}80`,
        }}
      />
    </div>
  );
};
