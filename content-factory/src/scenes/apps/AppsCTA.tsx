import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import { vis, getEnterTransform } from "../../utils/animations";

export const AppsCTA: React.FC<{
  line1: string;
  line2?: string;
  button?: string;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ line1, line2, button, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { colors } = theme;

  const l1Vis = vis(frame, fps, 5, durationFrames - 8);
  const l2Vis = vis(frame, fps, 15, durationFrames - 8);
  const btnVis = vis(frame, fps, 25, durationFrames - 8);

  const pulse = 1 + Math.sin(frame * 0.12) * 0.03;

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
        gap: 40,
      }}
    >
      {l1Vis.show && (
        <div
          style={{
            opacity: l1Vis.opacity,
            transform: getEnterTransform("zoomCenter", l1Vis.enter),
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
            {line1}
          </p>
        </div>
      )}
      {line2 && l2Vis.show && (
        <div
          style={{
            opacity: l2Vis.opacity,
            transform: getEnterTransform("slamBottom", l2Vis.enter),
          }}
        >
          <p
            style={{
              fontFamily: theme.fonts.heading,
              fontSize: 48,
              fontWeight: 700,
              color: colors.accent,
              margin: 0,
              textShadow: `0 0 20px ${colors.accent}40`,
            }}
          >
            {line2}
          </p>
        </div>
      )}
      {button && btnVis.show && (
        <div style={{ opacity: btnVis.opacity, transform: `scale(${btnVis.enter * pulse})` }}>
          <div
            style={{
              background: `linear-gradient(135deg, ${colors.accent}, ${colors.accentDark})`,
              borderRadius: 60,
              padding: "24px 60px",
              boxShadow: `0 8px 32px ${colors.accent}50`,
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
