import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import type { SceneDef } from "../../types/content";
import { vis, getEnterTransform, SNAPPY, float, breathe, glowPulse, tilt } from "../../utils/animations";
import { DataCard } from "../../components/DataCard";

export const GeographicScene: React.FC<{
  scene: SceneDef;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ scene, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { colors } = theme;

  // Fast staggered timing
  const locationVis = vis(frame, fps, 3, durationFrames - 8);
  const dataVis = vis(frame, fps, 12, durationFrames - 6);
  const textVis = vis(frame, fps, 28, durationFrames - 6);

  const location = String(scene.data?.location || scene.label);
  const entries = Object.entries(scene.data || {}).filter(
    ([k]) => k.startsWith("stat")
  );
  const cards =
    entries.length > 0
      ? entries.map(([, v]) => {
          const parts = String(v).split("|");
          return { label: parts[0], value: parts[1] || String(v) };
        })
      : [];

  const glow = glowPulse(frame, 0.08);
  const locationScale = breathe(frame, 0.04, 0.02);

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
      {locationVis.show && (
        <div
          style={{
            opacity: locationVis.opacity,
            transform: `${getEnterTransform("zoomCenter", locationVis.enter)} scale(${locationScale}) rotate(${tilt(frame, 0.02, 0.5)}deg)`,
          }}
        >
          <h1
            style={{
              fontFamily: theme.fonts.heading,
              fontSize: 90,
              fontWeight: 900,
              color: colors.accent,
              margin: 0,
              textTransform: "uppercase",
              letterSpacing: 6,
              textShadow: `0 0 ${30 + glow * 30}px ${colors.accent}50, 0 0 ${60 + glow * 40}px ${colors.accent}20`,
            }}
          >
            {location}
          </h1>
          {/* Underline that expands */}
          <div
            style={{
              height: 4,
              background: `linear-gradient(90deg, transparent, ${colors.accent}, transparent)`,
              marginTop: 8,
              opacity: locationVis.enter * glow,
              boxShadow: `0 0 12px ${colors.accent}60`,
            }}
          />
        </div>
      )}

      {/* Cards stagger in one by one */}
      {cards.length > 0 && dataVis.show && (
        <div
          style={{
            display: "flex",
            gap: 20,
            flexWrap: "wrap",
            justifyContent: "center",
            maxWidth: 900,
          }}
        >
          {cards.map((card, i) => (
            <DataCard
              key={i}
              label={card.label}
              value={card.value}
              theme={theme}
              enterAt={12}
              index={i}
            />
          ))}
        </div>
      )}

      {textVis.show && (
        <div
          style={{
            opacity: textVis.opacity,
            transform: `${getEnterTransform("slamBottom", textVis.enter)} translateY(${float(frame, 0.04, 3)}px)`,
            maxWidth: 850,
          }}
        >
          <p
            style={{
              fontFamily: theme.fonts.body,
              fontSize: 32,
              color: colors.textSoft,
              margin: 0,
              textAlign: "center",
              lineHeight: 1.4,
            }}
          >
            {scene.text}
          </p>
        </div>
      )}
    </div>
  );
};
