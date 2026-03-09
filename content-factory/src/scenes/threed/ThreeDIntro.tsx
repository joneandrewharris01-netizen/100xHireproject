import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import { FAST, SNAPPY, SMOOTH } from "../../utils/animations";

interface Props {
  hook: string;
  badge: string;
  theme: ThemeConfig;
  durationFrames: number;
}

export const ThreeDIntro: React.FC<Props> = ({
  hook,
  badge,
  theme,
  durationFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { colors } = theme;

  // Animated accent line sweeps across
  const lineSweep = spring({ frame: frame - 3, fps, config: SMOOTH });
  const lineWidth = interpolate(lineSweep, [0, 1], [0, 400]);

  // Badge enters with a snap
  const badgeEnter = spring({ frame: frame - 8, fps, config: SNAPPY });

  // Split hook into words for staggered reveal
  const words = hook.split(" ");
  const wordsPerLine = Math.ceil(words.length / 2);
  const line1 = words.slice(0, wordsPerLine).join(" ");
  const line2 = words.slice(wordsPerLine).join(" ");

  // Each line enters separately
  const line1Enter = spring({ frame: frame - 16, fps, config: FAST });
  const line2Enter = spring({ frame: frame - 24, fps, config: FAST });

  // Accent dot that pulses
  const dotPulse = interpolate(
    Math.sin(frame * 0.08),
    [-1, 1],
    [0.6, 1]
  );

  // Bottom accent bar grows
  const barEnter = spring({ frame: frame - 32, fps, config: SMOOTH });

  // Exit
  const exitProgress = interpolate(
    frame,
    [durationFrames - 12, durationFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const exitScale = 1 - exitProgress * 0.3;
  const exitOpacity = 1 - exitProgress;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 70px",
        opacity: exitOpacity,
        transform: `scale(${exitScale})`,
      }}
    >
      {/* Top accent line */}
      <div
        style={{
          width: lineWidth,
          height: 3,
          background: `linear-gradient(90deg, transparent, ${colors.accent}, transparent)`,
          marginBottom: 40,
          borderRadius: 2,
        }}
      />

      {/* Badge pill */}
      <div
        style={{
          opacity: badgeEnter,
          transform: `translateY(${(1 - badgeEnter) * -30}px) scale(${0.8 + 0.2 * badgeEnter})`,
          marginBottom: 32,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            background: `${colors.accent}12`,
            border: `1px solid ${colors.accent}35`,
            borderRadius: 50,
            padding: "10px 28px",
          }}
        >
          {/* Pulsing dot */}
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: colors.accent,
              boxShadow: `0 0 ${8 * dotPulse}px ${colors.accent}`,
              opacity: dotPulse,
            }}
          />
          <span
            style={{
              color: colors.accent,
              fontFamily: theme.fonts.mono,
              fontSize: 22,
              fontWeight: 700,
              letterSpacing: 3,
              textTransform: "uppercase",
            }}
          >
            {badge}
          </span>
        </div>
      </div>

      {/* Hook text — line by line with clip reveal */}
      <div style={{ textAlign: "center", maxWidth: 920 }}>
        {/* Line 1 */}
        <div
          style={{
            overflow: "hidden",
            marginBottom: 8,
          }}
        >
          <div
            style={{
              transform: `translateY(${(1 - line1Enter) * 100}%)`,
              opacity: line1Enter,
            }}
          >
            <span
              style={{
                fontFamily: theme.fonts.heading,
                fontSize: 68,
                fontWeight: 900,
                color: colors.text,
                lineHeight: 1.15,
              }}
            >
              {line1}
            </span>
          </div>
        </div>

        {/* Line 2 */}
        <div style={{ overflow: "hidden" }}>
          <div
            style={{
              transform: `translateY(${(1 - line2Enter) * 100}%)`,
              opacity: line2Enter,
            }}
          >
            <span
              style={{
                fontFamily: theme.fonts.heading,
                fontSize: 68,
                fontWeight: 900,
                color: colors.accent,
                lineHeight: 1.15,
              }}
            >
              {line2}
            </span>
          </div>
        </div>
      </div>

      {/* Bottom accent bar */}
      <div
        style={{
          marginTop: 40,
          width: interpolate(barEnter, [0, 1], [0, 200]),
          height: 4,
          background: `linear-gradient(90deg, ${colors.accentDark}, ${colors.accent}, ${colors.accentLight})`,
          borderRadius: 2,
          boxShadow: `0 0 20px ${colors.accent}40`,
        }}
      />
    </div>
  );
};
