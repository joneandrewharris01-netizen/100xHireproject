import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import type { ThemeConfig } from "../../types/themes";

export const Background: React.FC<{ theme: ThemeConfig }> = ({ theme }) => {
  const frame = useCurrentFrame();
  const { colors } = theme;

  // Slow-moving gradient center for subtle life
  const orbX = 50 + Math.sin(frame * 0.012) * 12;
  const orbY = 40 + Math.cos(frame * 0.015) * 8;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: `radial-gradient(ellipse at ${orbX}% ${orbY}%, ${colors.bgLight} 0%, ${colors.bg} 55%, ${colors.bgDark} 100%)`,
        overflow: "hidden",
      }}
    >
      {/* Soft accent glow orb */}
      <div
        style={{
          position: "absolute",
          top: `${orbY}%`,
          left: `${orbX}%`,
          width: 800,
          height: 800,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${colors.accent}10 0%, transparent 70%)`,
          transform: "translate(-50%, -50%)",
          opacity: 0.4,
        }}
      />
      {/* Secondary soft orb */}
      <div
        style={{
          position: "absolute",
          bottom: `${18 + Math.sin(frame * 0.014) * 6}%`,
          right: `${12 + Math.cos(frame * 0.018) * 8}%`,
          width: 500,
          height: 500,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${colors.accentDark || colors.accent}0C 0%, transparent 70%)`,
          opacity: 0.3,
        }}
      />
    </div>
  );
};
