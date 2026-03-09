import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import type { SceneDef } from "../../types/content";
import { vis, getEnterTransform } from "../../utils/animations";
import { TerminalBlock } from "../../components/TerminalBlock";

export const ClientStory: React.FC<{
  scene: SceneDef;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ scene, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerVis = vis(frame, fps, 5, durationFrames - 12);
  const termVis = vis(frame, fps, 15, durationFrames - 8);

  const lines = [
    `$ client-report --project "${scene.label}"`,
    "",
    scene.text,
    "",
    scene.data?.result ? `> Result: ${scene.data.result}` : "> Status: AUTOMATED",
    scene.data?.savings ? `> Savings: ${scene.data.savings}` : "",
  ].filter(Boolean);

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
      {headerVis.show && (
        <div
          style={{
            opacity: headerVis.opacity,
            transform: getEnterTransform("slamLeft", headerVis.enter),
          }}
        >
          <h2
            style={{
              fontFamily: theme.fonts.heading,
              fontSize: 48,
              fontWeight: 700,
              color: theme.colors.text,
              margin: 0,
              textAlign: "center",
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
          <TerminalBlock lines={lines} theme={theme} enterAt={15} />
        </div>
      )}
    </div>
  );
};
