import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import type { ThemeConfig } from "../types/themes";
import { FAST, breathe, glowPulse } from "../utils/animations";

export const PillBadge: React.FC<{
  text: string;
  theme: ThemeConfig;
  enterAt?: number;
}> = ({ text, theme, enterAt = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - enterAt, fps, config: FAST });
  const scale = breathe(frame, 0.07, 0.025);
  const glow = glowPulse(frame, 0.1);

  return (
    <div
      style={{
        display: "inline-block",
        background: `linear-gradient(135deg, ${theme.colors.accent}, ${theme.colors.accentDark})`,
        borderRadius: 50,
        padding: "16px 40px",
        transform: `scale(${enter * scale}) translateY(${(1 - enter) * -30}px)`,
        opacity: enter,
        boxShadow: `0 8px ${24 + glow * 16}px ${theme.colors.accent}${Math.round(40 + glow * 30).toString(16)}, 0 2px 8px rgba(0,0,0,0.4)`,
      }}
    >
      <span
        style={{
          color: theme.colors.bgDark,
          fontFamily: theme.fonts.heading,
          fontWeight: 800,
          fontSize: 32,
          letterSpacing: 2,
          textTransform: "uppercase",
        }}
      >
        {text}
      </span>
    </div>
  );
};
