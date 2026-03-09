import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import type { SceneDef } from "../../types/content";
import { vis, getEnterTransform, ANIM_CYCLE, SNAPPY, float, breathe, glowPulse } from "../../utils/animations";
import { DataCard } from "../../components/DataCard";
import { TerminalBlock } from "../../components/TerminalBlock";

export const ContentScene: React.FC<{
  scene: SceneDef;
  theme: ThemeConfig;
  durationFrames: number;
  index?: number;
}> = ({ scene, theme, durationFrames, index = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Tighter timing
  const headerVis = vis(frame, fps, 3, durationFrames - 8);
  const bodyVis = vis(frame, fps, 10, durationFrames - 6);
  const dataVis = vis(frame, fps, 16, durationFrames - 6);

  const animMode = ANIM_CYCLE[index % ANIM_CYCLE.length];
  const glow = glowPulse(frame, 0.07 + index * 0.01);

  const statEntries = Object.entries(scene.data || {}).filter(([k]) =>
    k.startsWith("stat")
  );
  const hasTerminal = scene.data?.terminal === "true";
  const termLines = scene.text.split("\n");

  // Word-by-word for body text
  const bodyWords = scene.text.split(" ");

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
        gap: 24,
      }}
    >
      {headerVis.show && (
        <div
          style={{
            opacity: headerVis.opacity,
            transform: `${getEnterTransform(animMode, headerVis.enter)} translateY(${float(frame, 0.05, 4)}px) scale(${breathe(frame, 0.04, 0.015)})`,
          }}
        >
          <h2
            style={{
              fontFamily: theme.fonts.heading,
              fontSize: 52,
              fontWeight: 800,
              color: theme.colors.accent,
              margin: 0,
              textAlign: "center",
              textShadow: `0 0 ${16 + glow * 20}px ${theme.colors.accent}40`,
            }}
          >
            {scene.label}
          </h2>
          {/* Accent underline */}
          <div
            style={{
              height: 3,
              background: `linear-gradient(90deg, transparent, ${theme.colors.accent}, transparent)`,
              marginTop: 10,
              opacity: headerVis.enter * glow,
            }}
          />
        </div>
      )}

      {bodyVis.show && !hasTerminal && statEntries.length > 0 && (
        <div
          style={{
            maxWidth: 850,
            textAlign: "center",
          }}
        >
          <p
            style={{
              fontFamily: theme.fonts.body,
              fontSize: 34,
              color: theme.colors.text,
              margin: 0,
              lineHeight: 1.4,
            }}
          >
            {bodyWords.map((word, i) => {
              const wordDelay = 10 + i * 1.5;
              const wordEnter = spring({ frame: frame - wordDelay, fps, config: SNAPPY });
              return (
                <span
                  key={i}
                  style={{
                    display: "inline-block",
                    opacity: Math.min(wordEnter, bodyVis.opacity),
                    transform: `translateY(${(1 - wordEnter) * 12}px)`,
                    marginRight: 7,
                  }}
                >
                  {word}
                </span>
              );
            })}
          </p>
        </div>
      )}

      {bodyVis.show && hasTerminal && (
        <div
          style={{
            opacity: bodyVis.opacity,
            display: "flex",
            justifyContent: "center",
            width: "100%",
            transform: `translateY(${float(frame, 0.03, 4)}px)`,
          }}
        >
          <TerminalBlock lines={termLines} theme={theme} enterAt={10} />
        </div>
      )}

      {/* Cards stagger in one by one with continuous float */}
      {statEntries.length > 0 && dataVis.show && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: statEntries.length > 2 ? "1fr 1fr" : "1fr",
            gap: 20,
            width: "90%",
          }}
        >
          {statEntries.map(([, v], i) => {
            const parts = String(v).split("|");
            return (
              <DataCard
                key={i}
                label={parts[0]}
                value={parts[1] || String(v)}
                theme={theme}
                enterAt={16}
                index={i}
              />
            );
          })}
        </div>
      )}

      {/* Body text shown below cards if no stat entries */}
      {bodyVis.show && !hasTerminal && statEntries.length === 0 && (
        <div
          style={{
            opacity: bodyVis.opacity,
            transform: `${getEnterTransform("slamBottom", bodyVis.enter)} translateY(${float(frame, 0.04, 3)}px)`,
            maxWidth: 850,
          }}
        >
          <p
            style={{
              fontFamily: theme.fonts.body,
              fontSize: 36,
              color: theme.colors.text,
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
