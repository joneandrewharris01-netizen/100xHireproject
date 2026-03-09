import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import { vis, getEnterTransform } from "../../utils/animations";
import { PillBadge } from "../../components/PillBadge";

export const AppsIntro: React.FC<{
  hook: string;
  badge: string;
  appName?: string;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ hook, badge, appName, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const badgeVis = vis(frame, fps, 8, durationFrames - 10);
  const hookVis = vis(frame, fps, 20, durationFrames - 8);
  const nameVis = vis(frame, fps, 35, durationFrames - 8);

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
        gap: 40,
      }}
    >
      {badgeVis.show && (
        <div style={{ opacity: badgeVis.opacity }}>
          <PillBadge text={badge} theme={theme} enterAt={8} />
        </div>
      )}
      {hookVis.show && (
        <div
          style={{
            opacity: hookVis.opacity,
            transform: getEnterTransform("slamBottom", hookVis.enter),
            textAlign: "center",
            maxWidth: 900,
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
            {hook}
          </p>
        </div>
      )}
      {appName && nameVis.show && (
        <div
          style={{
            opacity: nameVis.opacity,
            transform: getEnterTransform("zoomCenter", nameVis.enter),
          }}
        >
          <span
            style={{
              fontFamily: theme.fonts.mono,
              fontSize: 52,
              fontWeight: 700,
              color: theme.colors.accent,
              textShadow: `0 0 30px ${theme.colors.accent}50`,
            }}
          >
            {appName}
          </span>
        </div>
      )}
    </div>
  );
};
