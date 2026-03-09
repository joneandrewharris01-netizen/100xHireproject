import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  Img,
  OffthreadVideo,
  staticFile,
} from "remotion";
import type { ThemeConfig } from "../../types/themes";
import type { SceneDef } from "../../types/content";
import { FAST, SNAPPY } from "../../utils/animations";

/**
 * ToolShowcase — full-screen video b-roll with overlaid tool label.
 *
 * Layout:
 *   - Video fills the entire 1080x1920 frame
 *   - Tool name + brand float at top-center with dark gradient behind
 *   - Bottom area left clear for WordCaptions (handled externally)
 *   - No description text — captions cover the voiceover content
 */

const EXIT_DURATION = 8;

export const ToolShowcase: React.FC<{
  scene: SceneDef;
  theme: ThemeConfig;
  durationFrames: number;
  index?: number;
}> = ({ scene, theme, durationFrames, index = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { colors } = theme;

  const toolVideo = scene.data?.toolVideo as string | undefined;
  const toolImage = String(scene.data?.toolImage || "");
  const toolBrand = scene.data?.toolBrand as string | undefined;
  const hasVideo = !!toolVideo;
  const hasMedia = hasVideo || !!toolImage;

  // Enter animations
  const mediaEnter = spring({ frame: frame - 2, fps, config: FAST });
  const labelEnter = spring({ frame: frame - 8, fps, config: SNAPPY });
  const brandEnter = spring({ frame: frame - 14, fps, config: SNAPPY });

  // Exit animation
  const exitStart = durationFrames - EXIT_DURATION;
  const exitProgress = interpolate(frame, [exitStart, durationFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exitOpacity = 1 - exitProgress;
  const exitScale = 1 - exitProgress * 0.03;

  // Ken Burns for static images
  const zoom = interpolate(frame, [0, durationFrames], [1.0, 1.08], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        opacity: exitOpacity,
        transform: `scale(${exitScale})`,
      }}
    >
      {/* Full-screen video / screenshot background */}
      {hasMedia && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            opacity: mediaEnter,
            overflow: "hidden",
          }}
        >
          {hasVideo ? (
            <OffthreadVideo
              src={staticFile(toolVideo)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
              }}
              muted
            />
          ) : (
            <Img
              src={staticFile(toolImage)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                transform: `scale(${zoom})`,
                transformOrigin: "center center",
              }}
            />
          )}

          {/* Top gradient for text readability */}
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              height: 400,
              background: "linear-gradient(to bottom, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0.3) 60%, transparent 100%)",
            }}
          />

          {/* Bottom gradient for captions readability */}
          <div
            style={{
              position: "absolute",
              bottom: 0,
              left: 0,
              right: 0,
              height: 500,
              background: "linear-gradient(to top, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.3) 50%, transparent 100%)",
            }}
          />
        </div>
      )}

      {/* Tool label overlay — top area */}
      <div
        style={{
          position: "absolute",
          top: 80,
          left: 0,
          right: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 6,
          zIndex: 2,
        }}
      >
        {/* Brand label */}
        {toolBrand && (
          <div
            style={{
              opacity: brandEnter * exitOpacity,
              transform: `translateY(${(1 - brandEnter) * -20}px)`,
            }}
          >
            <span
              style={{
                fontFamily: theme.fonts.heading,
                fontSize: 26,
                fontWeight: 700,
                color: colors.accent,
                letterSpacing: 2,
                textTransform: "uppercase",
                textShadow: "0 2px 12px rgba(0,0,0,0.9)",
              }}
            >
              {toolBrand}
            </span>
          </div>
        )}

        {/* Tool name */}
        <div
          style={{
            opacity: labelEnter * exitOpacity,
            transform: `translateY(${(1 - labelEnter) * 25}px) scale(${0.9 + 0.1 * labelEnter})`,
          }}
        >
          <h2
            style={{
              fontFamily: theme.fonts.heading,
              fontSize: 80,
              fontWeight: 900,
              color: colors.text,
              margin: 0,
              lineHeight: 1.1,
              textAlign: "center",
              textShadow: "0 4px 24px rgba(0,0,0,0.95), 0 2px 8px rgba(0,0,0,0.8)",
            }}
          >
            {scene.label}
          </h2>
        </div>
      </div>
    </div>
  );
};
