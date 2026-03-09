import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import type { SceneDef } from "../../types/content";
import { vis, getEnterTransform } from "../../utils/animations";
import { DataCard } from "../../components/DataCard";

export const IdeaReveal: React.FC<{
  scene: SceneDef;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ scene, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleVis = vis(frame, fps, 5, durationFrames - 12);
  const descVis = vis(frame, fps, 18, durationFrames - 10);
  const cardsVis = vis(frame, fps, 28, durationFrames - 8);

  const revenue = String(scene.data?.revenue || "$10K/mo");
  const builder = String(scene.data?.builder || "1 person");

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
        gap: 36,
      }}
    >
      {titleVis.show && (
        <div
          style={{
            opacity: titleVis.opacity,
            transform: getEnterTransform("slamLeft", titleVis.enter),
          }}
        >
          <h2
            style={{
              fontFamily: theme.fonts.heading,
              fontSize: 56,
              fontWeight: 800,
              color: theme.colors.accent,
              margin: 0,
              textAlign: "center",
              textShadow: `0 0 20px ${theme.colors.accent}40`,
            }}
          >
            {scene.label}
          </h2>
        </div>
      )}
      {descVis.show && (
        <div
          style={{
            opacity: descVis.opacity,
            transform: getEnterTransform("slamRight", descVis.enter),
            maxWidth: 850,
          }}
        >
          <p
            style={{
              fontFamily: theme.fonts.body,
              fontSize: 36,
              color: theme.colors.textSoft,
              margin: 0,
              textAlign: "center",
              lineHeight: 1.4,
            }}
          >
            {scene.text}
          </p>
        </div>
      )}
      {cardsVis.show && (
        <div
          style={{
            display: "flex",
            gap: 24,
            opacity: cardsVis.opacity,
          }}
        >
          <DataCard label="Revenue" value={revenue} theme={theme} enterAt={28} index={0} />
          <DataCard label="Team" value={builder} theme={theme} enterAt={28} index={1} />
        </div>
      )}
    </div>
  );
};
