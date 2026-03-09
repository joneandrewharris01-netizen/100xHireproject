import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import type { ThemeConfig } from "../types/themes";
import { BOUNCY } from "../utils/animations";

export const HeroIcon: React.FC<{
  icon: string;
  theme: ThemeConfig;
  enterAt?: number;
  size?: number;
}> = ({ icon, theme, enterAt = 0, size = 80 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - enterAt, fps, config: BOUNCY });

  // Subtle beat pulse
  const beat = 1 + Math.sin((frame - enterAt) * 0.15) * 0.05;

  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: size / 2,
        background: `linear-gradient(135deg, ${theme.colors.accent}30, ${theme.colors.accentDark}20)`,
        border: `2px solid ${theme.colors.accent}50`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: size * 0.5,
        transform: `scale(${enter * beat})`,
        opacity: enter,
        boxShadow: `0 0 20px ${theme.colors.accent}20`,
      }}
    >
      {icon}
    </div>
  );
};
