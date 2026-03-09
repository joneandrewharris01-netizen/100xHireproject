import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import { vis, getEnterTransform, SNAPPY, float, breathe, sway, glowPulse } from "../../utils/animations";
import { PillBadge } from "../../components/PillBadge";

export const FinanceIntro: React.FC<{
  hook: string;
  badge: string;
  demographic?: string;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ hook, badge, demographic, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const badgeVis = vis(frame, fps, 4, durationFrames - 8);
  const demoVis = vis(frame, fps, 12, durationFrames - 8);
  const hookVis = vis(frame, fps, 18, durationFrames - 6);

  // Split hook into words for staggered reveal
  const hookWords = hook.split(" ");
  const glow = glowPulse(frame, 0.09);

  // Accent line animations
  const lineWidth = spring({ frame: frame - 6, fps, config: SNAPPY }) * 100;

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
      {/* Animated accent line */}
      <div
        style={{
          width: `${lineWidth}%`,
          height: 3,
          background: `linear-gradient(90deg, transparent, ${theme.colors.accent}, transparent)`,
          opacity: 0.6,
          marginBottom: 10,
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

      {demographic && demoVis.show && (
        <div
          style={{
            opacity: demoVis.opacity,
            transform: `${getEnterTransform("slamLeft", demoVis.enter)} translateX(${sway(frame, 0.04, 3)}px)`,
          }}
        >
          <p
            style={{
              fontFamily: theme.fonts.body,
              fontSize: 38,
              color: theme.colors.textSoft,
              margin: 0,
              textAlign: "center",
              fontStyle: "italic",
            }}
          >
            {demographic}
          </p>
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
              fontSize: 60,
              fontWeight: 800,
              color: theme.colors.text,
              lineHeight: 1.2,
              margin: 0,
            }}
          >
            {hookWords.map((word, i) => {
              const wordDelay = 18 + i * 2;
              const wordEnter = spring({ frame: frame - wordDelay, fps, config: SNAPPY });
              return (
                <span
                  key={i}
                  style={{
                    display: "inline-block",
                    opacity: wordEnter,
                    transform: `translateY(${(1 - wordEnter) * 20}px)`,
                    marginRight: 12,
                    textShadow: glow > 0.8 && i === hookWords.length - 1
                      ? `0 0 20px ${theme.colors.accent}40`
                      : "none",
                  }}
                >
                  {word}
                </span>
              );
            })}
          </p>
        </div>
      )}

      {/* Bottom accent line */}
      <div
        style={{
          width: `${lineWidth * 0.6}%`,
          height: 2,
          background: `linear-gradient(90deg, transparent, ${theme.colors.accent}60, transparent)`,
          opacity: 0.4,
          marginTop: 10,
        }}
      />
    </div>
  );
};
