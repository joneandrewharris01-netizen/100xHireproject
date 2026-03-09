import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import { FAST, SNAPPY } from "../../utils/animations";

export const WealthCTA: React.FC<{
  line1: string;
  line2?: string;
  button?: string;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ line1, line2, button, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { colors } = theme;

  const l1Enter = spring({ frame: frame - 5, fps, config: FAST });
  const l2Enter = spring({ frame: frame - 15, fps, config: SNAPPY });
  const btnEnter = spring({ frame: frame - 25, fps, config: SNAPPY });

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "80px 50px",
        gap: 32,
      }}
    >
      <div
        style={{
          opacity: l1Enter,
          transform: `translateY(${(1 - l1Enter) * 20}px)`,
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
            lineHeight: 1.1,
          }}
        >
          {line1}
        </p>
      </div>

      {line2 && (
        <div
          style={{
            opacity: l2Enter,
            transform: `translateY(${(1 - l2Enter) * 15}px)`,
          }}
        >
          <p
            style={{
              fontFamily: theme.fonts.heading,
              fontSize: 48,
              fontWeight: 700,
              color: colors.accent,
              margin: 0,
              textAlign: "center",
            }}
          >
            {line2}
          </p>
        </div>
      )}

      {button && (
        <div
          style={{
            opacity: btnEnter,
            transform: `scale(${0.9 + 0.1 * btnEnter}) translateY(${(1 - btnEnter) * 15}px)`,
            marginTop: 12,
          }}
        >
          <div
            style={{
              background: colors.accent,
              borderRadius: 60,
              padding: "22px 56px",
            }}
          >
            <span
              style={{
                fontFamily: theme.fonts.heading,
                fontSize: 34,
                fontWeight: 800,
                color: colors.bgDark,
                textTransform: "uppercase",
                letterSpacing: 2,
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
