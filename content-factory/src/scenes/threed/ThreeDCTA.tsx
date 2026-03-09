import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import type { ThemeConfig } from "../../types/themes";
import { FAST, SNAPPY, SMOOTH } from "../../utils/animations";

interface Props {
  line1: string;
  line2?: string;
  button?: string;
  theme: ThemeConfig;
  durationFrames: number;
}

export const ThreeDCTA: React.FC<Props> = ({
  line1,
  line2,
  button,
  theme,
  durationFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { colors } = theme;

  // Line 1: scale punch (overshoots then settles)
  const line1Enter = spring({
    frame: frame - 5,
    fps,
    config: { damping: 8, mass: 0.4, stiffness: 300 },
  });

  // Accent underline extends
  const underline = spring({ frame: frame - 12, fps, config: SMOOTH });

  // Line 2 slides up
  const line2Enter = spring({ frame: frame - 18, fps, config: FAST });

  // Button pops in
  const btnEnter = spring({ frame: frame - 26, fps, config: SNAPPY });

  // Button glow pulses
  const glowIntensity = interpolate(
    Math.sin(frame * 0.1),
    [-1, 1],
    [15, 40]
  );

  // Floating arrows around button
  const arrowBounce = interpolate(
    Math.sin(frame * 0.12),
    [-1, 1],
    [-4, 4]
  );

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
      }}
    >
      {/* Line 1 — punch scale entry */}
      <div
        style={{
          transform: `scale(${line1Enter})`,
          opacity: Math.min(line1Enter * 1.5, 1),
          textAlign: "center",
        }}
      >
        <span
          style={{
            fontFamily: theme.fonts.heading,
            fontSize: 64,
            fontWeight: 900,
            color: colors.text,
            lineHeight: 1.2,
          }}
        >
          {line1}
        </span>
      </div>

      {/* Animated underline */}
      <div
        style={{
          width: interpolate(underline, [0, 1], [0, 300]),
          height: 4,
          background: `linear-gradient(90deg, transparent, ${colors.accent}, transparent)`,
          marginTop: 16,
          marginBottom: 20,
          borderRadius: 2,
          boxShadow: `0 0 15px ${colors.accent}40`,
        }}
      />

      {/* Line 2 */}
      {line2 && (
        <div
          style={{
            opacity: line2Enter,
            transform: `translateY(${(1 - line2Enter) * 30}px)`,
            textAlign: "center",
          }}
        >
          <span
            style={{
              fontFamily: theme.fonts.heading,
              fontSize: 44,
              fontWeight: 700,
              color: colors.accent,
              lineHeight: 1.3,
            }}
          >
            {line2}
          </span>
        </div>
      )}

      {/* Button with glow */}
      {button && (
        <div
          style={{
            marginTop: 44,
            opacity: btnEnter,
            transform: `scale(${0.7 + 0.3 * btnEnter}) translateY(${(1 - btnEnter) * 20}px)`,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 14,
              padding: "22px 52px",
              borderRadius: 60,
              background: `linear-gradient(135deg, ${colors.accent}, ${colors.accentDark})`,
              boxShadow: `0 0 ${glowIntensity}px ${colors.accent}50, 0 10px 30px rgba(0,0,0,0.4)`,
            }}
          >
            <span
              style={{
                fontFamily: theme.fonts.heading,
                fontSize: 30,
                fontWeight: 800,
                color: "#FFFFFF",
              }}
            >
              {button}
            </span>
            {/* Animated arrow */}
            <span
              style={{
                fontSize: 28,
                color: "#FFFFFF",
                transform: `translateX(${arrowBounce}px)`,
                display: "inline-block",
              }}
            >
              →
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
