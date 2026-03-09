import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import type { ThemeConfig } from "../types/themes";
import { FAST, breathe, glowPulse } from "../utils/animations";

export const NumberReveal: React.FC<{
  value: number;
  prefix?: string;
  suffix?: string;
  theme: ThemeConfig;
  enterAt?: number;
  fontSize?: number;
}> = ({ value, prefix = "", suffix = "", theme, enterAt = 0, fontSize = 120 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - enterAt, fps, config: FAST });

  // Count up
  const countProgress = spring({
    frame: frame - enterAt,
    fps,
    config: { damping: 30, mass: 1, stiffness: 80 },
  });
  const displayValue = Math.round(value * countProgress);
  const formatted = displayValue.toLocaleString("en-US");

  // Continuous motion
  const scale = breathe(frame, 0.05, 0.03);
  const glow = glowPulse(frame, 0.08);
  const glowSize = 30 + glow * 30;

  return (
    <div
      style={{
        transform: `scale(${(0.5 + 0.5 * enter) * scale})`,
        opacity: enter,
        textAlign: "center",
      }}
    >
      <span
        style={{
          fontFamily: theme.fonts.heading,
          fontSize,
          fontWeight: 900,
          color: theme.colors.accent,
          textShadow: `0 0 ${glowSize}px ${theme.colors.accent}60, 0 0 ${glowSize * 2}px ${theme.colors.accent}30`,
          letterSpacing: -2,
        }}
      >
        {prefix}
        {formatted}
        {suffix}
      </span>
    </div>
  );
};
