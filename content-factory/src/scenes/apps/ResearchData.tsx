import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import type { SceneDef } from "../../types/content";
import { vis, getEnterTransform } from "../../utils/animations";
import { DataCard } from "../../components/DataCard";

export const ResearchData: React.FC<{
  scene: SceneDef;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ scene, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerVis = vis(frame, fps, 5, durationFrames - 12);

  // Parse data entries from scene
  const entries = Object.entries(scene.data || {}).filter(
    ([k]) => k.startsWith("stat")
  );
  // Fallback data cards
  const cards =
    entries.length > 0
      ? entries.map(([k, v]) => {
          const parts = String(v).split("|");
          return { label: parts[0] || k, value: parts[1] || String(v) };
        })
      : [
          { label: "Apps Analyzed", value: "50+" },
          { label: "Avg Revenue", value: "$12K/mo" },
          { label: "Solo Founders", value: "78%" },
          { label: "AI-Built", value: "42%" },
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
        gap: 36,
      }}
    >
      {headerVis.show && (
        <div
          style={{
            opacity: headerVis.opacity,
            transform: getEnterTransform("slamLeft", headerVis.enter),
            marginBottom: 20,
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
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 24,
          width: "90%",
        }}
      >
        {cards.map((card, i) => (
          <DataCard
            key={i}
            label={card.label}
            value={card.value}
            theme={theme}
            enterAt={15}
            index={i}
          />
        ))}
      </div>
    </div>
  );
};
