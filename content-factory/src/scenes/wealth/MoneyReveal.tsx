import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import type { SceneDef } from "../../types/content";
import { vis, getEnterTransform } from "../../utils/animations";
import { NumberReveal } from "../../components/NumberReveal";

export const MoneyReveal: React.FC<{
  scene: SceneDef;
  theme: ThemeConfig;
  durationFrames: number;
}> = ({ scene, theme, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const labelVis = vis(frame, fps, 5, durationFrames - 12);
  const numberVis = vis(frame, fps, 12, durationFrames - 8);
  const subVis = vis(frame, fps, 25, durationFrames - 8);

  const amount = Number(scene.data?.amount) || 4000;
  const period = String(scene.data?.period || "/month");

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
      {labelVis.show && (
        <div
          style={{
            opacity: labelVis.opacity,
            transform: getEnterTransform("slamTop", labelVis.enter),
          }}
        >
          <p
            style={{
              fontFamily: theme.fonts.heading,
              fontSize: 36,
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
      {numberVis.show && (
        <div style={{ opacity: numberVis.opacity }}>
          <NumberReveal
            value={amount}
            prefix="$"
            suffix={period}
            theme={theme}
            enterAt={12}
            fontSize={130}
          />
        </div>
      )}
      {subVis.show && (
        <div
          style={{
            opacity: subVis.opacity,
            transform: getEnterTransform("slamBottom", subVis.enter),
          }}
        >
          <p
            style={{
              fontFamily: theme.fonts.body,
              fontSize: 34,
              color: theme.colors.text,
              margin: 0,
              textAlign: "center",
              maxWidth: 800,
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
