import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import { vis, getEnterTransform, SNAPPY, breathe, glowPulse, float } from "../../utils/animations";

export const FinanceCTA: React.FC<{
  line1: string;
  line2?: string;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ line1, line2, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { colors } = theme;

  const l1Vis = vis(frame, fps, 3, durationFrames - 6);
  const l2Vis = vis(frame, fps, 12, durationFrames - 6);

  const scale = breathe(frame, 0.06, 0.025);
  const glow = glowPulse(frame, 0.1);
  const shimmerX = (frame * 3) % 1200 - 200;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 80,
        gap: 30,
        overflow: "hidden",
      }}
    >
      {/* Shimmer sweep */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: shimmerX,
          width: 200,
          height: "100%",
          background: `linear-gradient(90deg, transparent, ${colors.accent}08, transparent)`,
          transform: "skewX(-15deg)",
        }}
      />

      {l1Vis.show && (
        <div
          style={{
            opacity: l1Vis.opacity,
            transform: `${getEnterTransform("zoomCenter", l1Vis.enter)} scale(${scale}) translateY(${float(frame, 0.05, 4)}px)`,
          }}
        >
          {/* Word-by-word reveal */}
          <p
            style={{
              fontFamily: theme.fonts.heading,
              fontSize: 64,
              fontWeight: 900,
              color: colors.text,
              margin: 0,
              textAlign: "center",
              maxWidth: 800,
              lineHeight: 1.2,
            }}
          >
            {line1.split(" ").map((word, i) => {
              const wordEnter = spring({ frame: frame - (3 + i * 3), fps, config: SNAPPY });
              return (
                <span
                  key={i}
                  style={{
                    display: "inline-block",
                    opacity: wordEnter,
                    transform: `translateY(${(1 - wordEnter) * 25}px) scale(${0.8 + wordEnter * 0.2})`,
                    marginRight: 14,
                  }}
                >
                  {word}
                </span>
              );
            })}
          </p>
        </div>
      )}
      {line2 && l2Vis.show && (
        <div
          style={{
            opacity: l2Vis.opacity * (0.7 + glow * 0.3),
            transform: `${getEnterTransform("slamBottom", l2Vis.enter)} scale(${scale})`,
          }}
        >
          <p
            style={{
              fontFamily: theme.fonts.heading,
              fontSize: 44,
              fontWeight: 700,
              color: colors.accent,
              margin: 0,
              textAlign: "center",
              textShadow: `0 0 ${20 + glow * 20}px ${colors.accent}50`,
            }}
          >
            {line2}
          </p>
        </div>
      )}
    </div>
  );
};
