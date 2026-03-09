import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import { vis, getEnterTransform, SNAPPY, breathe, glowPulse, float } from "../../utils/animations";

export const CustomCTA: React.FC<{
  line1: string;
  line2?: string;
  button?: string;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ line1, line2, button, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { colors } = theme;

  const l1Vis = vis(frame, fps, 3, durationFrames - 6);
  const l2Vis = vis(frame, fps, 10, durationFrames - 6);
  const btnVis = vis(frame, fps, 18, durationFrames - 6);

  const scale = breathe(frame, 0.06, 0.025);
  const glow = glowPulse(frame, 0.1);
  const pulse = 1 + Math.sin(frame * 0.12) * 0.04;
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
          <p
            style={{
              fontFamily: theme.fonts.heading,
              fontSize: 72,
              fontWeight: 900,
              color: colors.text,
              margin: 0,
              textAlign: "center",
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
              fontSize: 48,
              fontWeight: 700,
              color: colors.accent,
              margin: 0,
              textShadow: `0 0 ${20 + glow * 20}px ${colors.accent}50`,
            }}
          >
            {line2}
          </p>
        </div>
      )}
      {button && btnVis.show && (
        <div
          style={{
            opacity: btnVis.opacity,
            transform: `scale(${btnVis.enter * pulse}) translateY(${float(frame, 0.06, 3)}px)`,
          }}
        >
          <div
            style={{
              background: `linear-gradient(135deg, ${colors.accent}, ${colors.accentDark})`,
              borderRadius: 60,
              padding: "24px 60px",
              boxShadow: `0 8px ${24 + glow * 16}px ${colors.accent}50`,
            }}
          >
            <span
              style={{
                fontFamily: theme.fonts.heading,
                fontSize: 36,
                fontWeight: 800,
                color: colors.bgDark,
                textTransform: "uppercase",
              }}
            >
              {button}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
