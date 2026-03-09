import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import type { SceneDef } from "../../types/content";
import { vis, getEnterTransform, SNAPPY, float, breathe, glowPulse } from "../../utils/animations";
import { TerminalBlock } from "../../components/TerminalBlock";

export const AIAnalysis: React.FC<{
  scene: SceneDef;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ scene, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const promptVis = vis(frame, fps, 3, durationFrames - 8);
  const resultVis = vis(frame, fps, 12, durationFrames - 6);

  const prompt = String(scene.data?.prompt || "Analyze this financial data...");
  const result = String(scene.data?.result || scene.text);

  const lines = [
    `$ ask-ai "${prompt}"`,
    "",
    "> Analyzing...",
    "",
    `> ${result}`,
  ];

  const glow = glowPulse(frame, 0.08);

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
        gap: 28,
      }}
    >
      {promptVis.show && (
        <div
          style={{
            opacity: promptVis.opacity,
            transform: `${getEnterTransform("slamLeft", promptVis.enter)} translateY(${float(frame, 0.05, 3)}px) scale(${breathe(frame, 0.04, 0.01)})`,
          }}
        >
          {/* AI icon indicator */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 16,
            }}
          >
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                background: theme.colors.accent,
                boxShadow: `0 0 ${8 + glow * 12}px ${theme.colors.accent}80`,
              }}
            />
            <h2
              style={{
                fontFamily: theme.fonts.heading,
                fontSize: 44,
                fontWeight: 700,
                color: theme.colors.text,
                margin: 0,
                textAlign: "center",
              }}
            >
              {scene.label}
            </h2>
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                background: theme.colors.accent,
                boxShadow: `0 0 ${8 + glow * 12}px ${theme.colors.accent}80`,
              }}
            />
          </div>
        </div>
      )}
      {resultVis.show && (
        <div
          style={{
            opacity: resultVis.opacity,
            display: "flex",
            justifyContent: "center",
            width: "100%",
            transform: `translateY(${float(frame, 0.03, 4)}px)`,
          }}
        >
          <TerminalBlock lines={lines} theme={theme} enterAt={12} />
        </div>
      )}
    </div>
  );
};
