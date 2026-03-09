import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import type { ThemeConfig } from "../../types/themes";
import type { SceneDef } from "../../types/content";
import { FAST, SNAPPY, SMOOTH } from "../../utils/animations";

interface Props {
  scene: SceneDef;
  theme: ThemeConfig;
  durationFrames: number;
  sceneIndex: number;
}

// Animated number counter
const Counter: React.FC<{
  value: string;
  frame: number;
  fps: number;
  enterAt: number;
  theme: ThemeConfig;
}> = ({ value, frame, fps, enterAt, theme }) => {
  const enter = spring({ frame: frame - enterAt, fps, config: FAST });
  const { colors } = theme;

  // Try to extract number for count-up effect
  const numMatch = value.match(/^(\$?)(\d[\d,]*)(.*)/);

  if (numMatch) {
    const [, prefix, numStr, suffix] = numMatch;
    const num = parseInt(numStr.replace(/,/g, ""), 10);
    const countUp = spring({
      frame: frame - enterAt,
      fps,
      config: { damping: 30, mass: 1, stiffness: 80 },
    });
    const display = Math.round(num * countUp).toLocaleString("en-US");

    return (
      <span
        style={{
          fontFamily: theme.fonts.mono,
          fontSize: 52,
          fontWeight: 800,
          color: colors.accent,
          opacity: enter,
          textShadow: `0 0 30px ${colors.accent}50`,
        }}
      >
        {prefix}
        {display}
        {suffix}
      </span>
    );
  }

  return (
    <span
      style={{
        fontFamily: theme.fonts.mono,
        fontSize: 52,
        fontWeight: 800,
        color: colors.accent,
        opacity: enter,
      }}
    >
      {value}
    </span>
  );
};

export const ThreeDContent: React.FC<Props> = ({
  scene,
  theme,
  durationFrames,
  sceneIndex,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { colors } = theme;

  const dataEntries = scene.data ? Object.entries(scene.data) : [];
  const fromLeft = sceneIndex % 2 === 0;

  // Label slides in from side
  const labelEnter = spring({ frame: frame - 5, fps, config: SNAPPY });
  const labelSlide = fromLeft
    ? interpolate(labelEnter, [0, 1], [-200, 0])
    : interpolate(labelEnter, [0, 1], [200, 0]);

  // Horizontal line extends from label
  const lineEnter = spring({ frame: frame - 10, fps, config: SMOOTH });

  // Main text fades up
  const textEnter = spring({ frame: frame - 15, fps, config: FAST });

  // Cards stagger in from bottom
  const cardBaseDelay = 22;

  // Exit
  const exitProgress = interpolate(
    frame,
    [durationFrames - 12, durationFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const exitOpacity = 1 - exitProgress;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 60px",
        opacity: exitOpacity,
      }}
    >
      {/* Scene label with side accent */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          marginBottom: 20,
          opacity: labelEnter,
          transform: `translateX(${labelSlide}px)`,
        }}
      >
        <div
          style={{
            width: interpolate(lineEnter, [0, 1], [0, 50]),
            height: 2,
            background: colors.accent,
          }}
        />
        <span
          style={{
            fontFamily: theme.fonts.mono,
            fontSize: 26,
            fontWeight: 700,
            color: colors.accent,
            letterSpacing: 4,
            textTransform: "uppercase",
          }}
        >
          {scene.label}
        </span>
        <div
          style={{
            width: interpolate(lineEnter, [0, 1], [0, 50]),
            height: 2,
            background: colors.accent,
          }}
        />
      </div>

      {/* Main text */}
      <div
        style={{
          opacity: textEnter,
          transform: `translateY(${(1 - textEnter) * 40}px)`,
          fontSize: 48,
          fontWeight: 800,
          color: colors.text,
          textAlign: "center",
          lineHeight: 1.25,
          maxWidth: 880,
          marginBottom: dataEntries.length > 0 ? 36 : 0,
        }}
      >
        {scene.text}
      </div>

      {/* Data cards — glassmorphism style */}
      {dataEntries.length > 0 && (
        <div
          style={{
            display: "flex",
            gap: 20,
            flexWrap: "wrap",
            justifyContent: "center",
          }}
        >
          {dataEntries.map(([key, val], i) => {
            const cardDelay = cardBaseDelay + i * 6;
            const cardEnter = spring({
              frame: frame - cardDelay,
              fps,
              config: SNAPPY,
            });

            // Progress bar inside card
            const fillProgress = spring({
              frame: frame - cardDelay - 5,
              fps,
              config: { damping: 25, mass: 1, stiffness: 60 },
            });

            return (
              <div
                key={key}
                style={{
                  opacity: cardEnter,
                  transform: `translateY(${(1 - cardEnter) * 60}px) scale(${0.9 + 0.1 * cardEnter})`,
                  background: `linear-gradient(135deg, ${colors.surface}E6, ${colors.surfaceAlpha80})`,
                  backdropFilter: "blur(20px)",
                  border: `1px solid ${colors.accent}25`,
                  borderRadius: 20,
                  padding: "22px 32px",
                  minWidth: 180,
                  textAlign: "center",
                  position: "relative" as const,
                  overflow: "hidden",
                }}
              >
                {/* Top accent line inside card */}
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: `${fillProgress * 100}%`,
                    height: 3,
                    background: `linear-gradient(90deg, ${colors.accent}, ${colors.accentLight})`,
                    borderRadius: "20px 0 0 0",
                  }}
                />

                {/* Value with counter animation */}
                <div style={{ marginBottom: 6, marginTop: 4 }}>
                  <Counter
                    value={String(val)}
                    frame={frame}
                    fps={fps}
                    enterAt={cardDelay + 3}
                    theme={theme}
                  />
                </div>

                {/* Label */}
                <div
                  style={{
                    fontSize: 18,
                    fontWeight: 600,
                    color: colors.muted,
                    textTransform: "uppercase",
                    letterSpacing: 2,
                  }}
                >
                  {key}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
