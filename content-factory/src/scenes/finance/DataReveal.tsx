import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import type { SceneDef } from "../../types/content";
import { vis, getEnterTransform, SNAPPY, float, breathe, glowPulse } from "../../utils/animations";
import { NumberReveal } from "../../components/NumberReveal";

export const DataReveal: React.FC<{
  scene: SceneDef;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ scene, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Tighter timing — elements appear faster
  const labelVis = vis(frame, fps, 3, durationFrames - 8);
  const numberVis = vis(frame, fps, 10, durationFrames - 6);
  const descVis = vis(frame, fps, 22, durationFrames - 6);

  const bigNumber = Number(scene.data?.amount) || 0;
  const prefix = String(scene.data?.prefix || "");
  const suffix = String(scene.data?.suffix || "");
  const glow = glowPulse(frame, 0.07);

  // Split description text for staggered word reveal
  const descWords = scene.text.split(" ");

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
      {labelVis.show && (
        <div
          style={{
            opacity: labelVis.opacity,
            transform: `${getEnterTransform("slamTop", labelVis.enter)} translateY(${float(frame, 0.05, 3)}px)`,
          }}
        >
          <p
            style={{
              fontFamily: theme.fonts.heading,
              fontSize: 40,
              color: theme.colors.textSoft,
              margin: 0,
              textTransform: "uppercase",
              letterSpacing: 3,
            }}
          >
            {scene.label}
          </p>
        </div>
      )}

      {/* Pulsing accent line before number */}
      {numberVis.show && (
        <div
          style={{
            width: 120,
            height: 3,
            background: theme.colors.accent,
            opacity: glow * labelVis.opacity,
            boxShadow: `0 0 12px ${theme.colors.accent}60`,
          }}
        />
      )}

      {numberVis.show && bigNumber > 0 && (
        <div
          style={{
            opacity: numberVis.opacity,
            transform: `scale(${breathe(frame, 0.05, 0.025)})`,
          }}
        >
          <NumberReveal
            value={bigNumber}
            prefix={prefix}
            suffix={suffix}
            theme={theme}
            enterAt={10}
            fontSize={120}
          />
        </div>
      )}

      {descVis.show && (
        <div
          style={{
            maxWidth: 800,
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
            {descWords.map((word, i) => {
              const wordDelay = 22 + i * 1.5;
              const wordEnter = spring({ frame: frame - wordDelay, fps, config: SNAPPY });
              return (
                <span
                  key={i}
                  style={{
                    display: "inline-block",
                    opacity: Math.min(wordEnter, descVis.opacity),
                    transform: `translateY(${(1 - wordEnter) * 15}px)`,
                    marginRight: 8,
                  }}
                >
                  {word}
                </span>
              );
            })}
          </p>
        </div>
      )}
    </div>
  );
};
