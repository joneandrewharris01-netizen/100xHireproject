import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import { vis, SNAPPY, float, breathe, glowPulse } from "../../utils/animations";
import { PillBadge } from "../../components/PillBadge";

export const CustomIntro: React.FC<{
  hook: string;
  badge: string;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ hook, badge, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const badgeVis = vis(frame, fps, 4, durationFrames - 8);
  const hookVis = vis(frame, fps, 14, durationFrames - 6);

  const hookWords = hook.split(" ");
  const glow = glowPulse(frame, 0.08);
  const lineExpand = spring({ frame: frame - 6, fps, config: SNAPPY });

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 60,
        gap: 30,
      }}
    >
      {/* Expanding accent line */}
      <div
        style={{
          width: `${lineExpand * 80}%`,
          height: 3,
          background: `linear-gradient(90deg, transparent, ${theme.colors.accent}, transparent)`,
          opacity: 0.5 + glow * 0.3,
        }}
      />

      {badgeVis.show && (
        <div
          style={{
            opacity: badgeVis.opacity,
            transform: `translateY(${float(frame, 0.05, 4)}px)`,
          }}
        >
          <PillBadge text={badge} theme={theme} enterAt={4} />
        </div>
      )}

      {hookVis.show && (
        <div
          style={{
            textAlign: "center",
            maxWidth: 900,
            transform: `scale(${breathe(frame, 0.04, 0.01)})`,
          }}
        >
          <p
            style={{
              fontFamily: theme.fonts.heading,
              fontSize: 64,
              fontWeight: 800,
              color: theme.colors.text,
              lineHeight: 1.2,
              margin: 0,
            }}
          >
            {hookWords.map((word, i) => {
              const wordDelay = 14 + i * 2;
              const wordEnter = spring({ frame: frame - wordDelay, fps, config: SNAPPY });
              return (
                <span
                  key={i}
                  style={{
                    display: "inline-block",
                    opacity: wordEnter,
                    transform: `translateY(${(1 - wordEnter) * 22}px)`,
                    marginRight: 12,
                  }}
                >
                  {word}
                </span>
              );
            })}
          </p>
        </div>
      )}

      <div
        style={{
          width: `${lineExpand * 50}%`,
          height: 2,
          background: `linear-gradient(90deg, transparent, ${theme.colors.accent}60, transparent)`,
          opacity: 0.3 + glow * 0.2,
          marginTop: 10,
        }}
      />
    </div>
  );
};
