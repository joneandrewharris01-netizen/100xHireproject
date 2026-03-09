import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import type { ThemeConfig } from "../types/themes";
import { SNAPPY, float, breathe, glowPulse } from "../utils/animations";

export const DataCard: React.FC<{
  label: string;
  value: string;
  theme: ThemeConfig;
  enterAt?: number;
  index?: number;
}> = ({ label, value, theme, enterAt = 0, index = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const staggerDelay = enterAt + index * 8;
  const enter = spring({ frame: frame - staggerDelay, fps, config: SNAPPY });
  const { colors } = theme;

  // Each card floats at a different phase
  const floatY = float(frame, 0.04 + index * 0.005, 5);
  const scale = breathe(frame, 0.06 + index * 0.01, 0.015);
  const glow = glowPulse(frame, 0.07 + index * 0.02);
  const borderOpacity = Math.round(30 + glow * 40);

  return (
    <div
      style={{
        background: colors.surfaceAlpha80,
        borderRadius: 20,
        padding: "24px 32px",
        border: `1px solid ${colors.accent}${borderOpacity.toString(16).padStart(2, "0")}`,
        boxShadow: `0 8px 24px rgba(0,0,0,0.3), 0 0 ${12 + glow * 12}px ${colors.accent}15`,
        transform: `translateY(${(1 - enter) * 60 + floatY}px) scale(${enter * scale})`,
        opacity: enter,
        minWidth: 200,
      }}
    >
      <div
        style={{
          fontFamily: theme.fonts.body,
          fontSize: 22,
          color: colors.muted,
          marginBottom: 8,
          textTransform: "uppercase",
          letterSpacing: 1.5,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: theme.fonts.heading,
          fontSize: 44,
          fontWeight: 800,
          color: colors.accent,
          textShadow: `0 0 ${16 + glow * 20}px ${colors.accent}40`,
        }}
      >
        {value}
      </div>
    </div>
  );
};
