import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import { FAST, SNAPPY } from "../../utils/animations";

const EXIT_DURATION = 8;

export const WealthIntro: React.FC<{
  hook: string;
  badge: string;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ hook, badge, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { colors } = theme;

  const badgeEnter = spring({ frame: frame - 6, fps, config: FAST });
  const hookEnter = spring({ frame: frame - 18, fps, config: SNAPPY });

  // Exit animation
  const exitStart = durationFrames - EXIT_DURATION;
  const exitProgress = interpolate(frame, [exitStart, durationFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exitOpacity = 1 - exitProgress;
  const exitScale = 1 - exitProgress * 0.05;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "60px 50px",
        gap: 36,
        opacity: exitOpacity,
        transform: `scale(${exitScale})`,
      }}
    >
      {/* Clean badge */}
      <div
        style={{
          opacity: badgeEnter,
          transform: `translateY(${(1 - badgeEnter) * -20}px)`,
        }}
      >
        <div
          style={{
            display: "inline-block",
            background: colors.accent,
            borderRadius: 50,
            padding: "14px 36px",
          }}
        >
          <span
            style={{
              color: colors.bgDark,
              fontFamily: theme.fonts.heading,
              fontWeight: 800,
              fontSize: 28,
              letterSpacing: 2,
              textTransform: "uppercase",
            }}
          >
            {badge}
          </span>
        </div>
      </div>

      {/* Hook text */}
      <div
        style={{
          opacity: hookEnter,
          transform: `translateY(${(1 - hookEnter) * 25}px)`,
          textAlign: "center",
          maxWidth: 900,
        }}
      >
        <p
          style={{
            fontFamily: theme.fonts.heading,
            fontSize: 62,
            fontWeight: 800,
            color: colors.text,
            lineHeight: 1.2,
            margin: 0,
          }}
        >
          {hook}
        </p>
      </div>
    </div>
  );
};
