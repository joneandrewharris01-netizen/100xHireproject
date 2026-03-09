import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import type { SceneDef } from "../../types/content";
import { vis, getEnterTransform, FAST } from "../../utils/animations";
import { TerminalBlock } from "../../components/TerminalBlock";

export const SpeedBuild: React.FC<{
  scene: SceneDef;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ scene, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerVis = vis(frame, fps, 5, durationFrames - 12);
  const termVis = vis(frame, fps, 12, durationFrames - 8);
  const timerVis = vis(frame, fps, 12, durationFrames - 8);

  // Timer counting up
  const buildTime = String(scene.data?.buildTime || "2 hours");
  const elapsed = interpolate(frame, [12, durationFrames - 10], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const codeLines = [
    "$ claude-code --init new-app",
    "",
    "> Scaffolding project...",
    "> Installing dependencies...",
    "> Building MVP features...",
    `> Time: ${buildTime}`,
    "",
    "✓ App deployed successfully",
  ];

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
      {headerVis.show && (
        <div
          style={{
            opacity: headerVis.opacity,
            transform: getEnterTransform("slamTop", headerVis.enter),
          }}
        >
          <h2
            style={{
              fontFamily: theme.fonts.heading,
              fontSize: 44,
              fontWeight: 700,
              color: theme.colors.text,
              margin: 0,
            }}
          >
            {scene.label}
          </h2>
        </div>
      )}
      {termVis.show && (
        <div
          style={{
            opacity: termVis.opacity,
            display: "flex",
            justifyContent: "center",
            width: "100%",
          }}
        >
          <TerminalBlock lines={codeLines} theme={theme} enterAt={12} />
        </div>
      )}
      {/* Timer overlay */}
      {timerVis.show && (
        <div
          style={{
            position: "absolute",
            top: 100,
            right: 60,
            opacity: timerVis.opacity,
            background: theme.colors.surfaceAlpha80,
            borderRadius: 16,
            padding: "12px 24px",
            border: `1px solid ${theme.colors.accent}40`,
          }}
        >
          <span
            style={{
              fontFamily: theme.fonts.mono,
              fontSize: 28,
              color: theme.colors.accent,
            }}
          >
            {Math.floor(elapsed)}%
          </span>
        </div>
      )}
    </div>
  );
};
