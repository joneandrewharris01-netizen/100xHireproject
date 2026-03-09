import React from "react";
import { useCurrentFrame, useVideoConfig, spring } from "remotion";
import type { ThemeConfig } from "../types/themes";
import { FAST, float, glowPulse } from "../utils/animations";

export const TerminalBlock: React.FC<{
  lines: string[];
  theme: ThemeConfig;
  enterAt?: number;
}> = ({ lines, theme, enterAt = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { colors } = theme;
  const enter = spring({ frame: frame - enterAt, fps, config: FAST });

  // Typing effect: faster
  const elapsed = frame - enterAt;
  const charsPerFrame = 2.2;
  const totalChars = Math.floor(elapsed * charsPerFrame);

  let charCount = 0;
  const visibleLines = lines.map((line) => {
    const start = charCount;
    charCount += line.length;
    if (totalChars >= charCount) return line;
    if (totalChars <= start) return "";
    return line.slice(0, totalChars - start);
  });

  // Continuous motion
  const floatY = float(frame, 0.03, 4);
  const glow = glowPulse(frame, 0.06);

  return (
    <div
      style={{
        background: colors.termBg,
        borderRadius: 16,
        border: `1px solid ${colors.termBorder}`,
        boxShadow: `0 12px 40px rgba(0,0,0,0.5), 0 0 ${40 + glow * 30}px ${colors.accent}10`,
        overflow: "hidden",
        transform: `scale(${0.8 + 0.2 * enter}) translateY(${floatY}px)`,
        opacity: enter,
        width: "90%",
      }}
    >
      {/* Title bar with breathing dots */}
      <div
        style={{
          display: "flex",
          gap: 8,
          padding: "12px 16px",
          borderBottom: `1px solid ${colors.termBorder}`,
        }}
      >
        {["#FF5F57", "#FFBD2E", "#28CA42"].map((c, i) => (
          <div
            key={i}
            style={{
              width: 12,
              height: 12,
              borderRadius: 6,
              background: c,
              boxShadow: `0 0 ${4 + Math.sin(frame * 0.1 + i) * 3}px ${c}80`,
            }}
          />
        ))}
      </div>
      {/* Content with line-by-line reveal */}
      <div style={{ padding: "20px 24px" }}>
        {visibleLines.map((line, i) => (
          <div
            key={i}
            style={{
              fontFamily: theme.fonts.mono,
              fontSize: 28,
              color: line.startsWith("$")
                ? colors.termAccent
                : line.startsWith(">")
                ? colors.accent
                : colors.termText,
              lineHeight: 1.6,
              whiteSpace: "pre-wrap",
              textShadow: line.startsWith(">")
                ? `0 0 8px ${colors.accent}40`
                : "none",
            }}
          >
            {line || "\u00A0"}
            {i === visibleLines.length - 1 && totalChars < charCount && (
              <span
                style={{
                  display: "inline-block",
                  width: 14,
                  height: 28,
                  background: colors.termAccent,
                  marginLeft: 2,
                  opacity: Math.sin(frame * 0.25) > 0 ? 1 : 0,
                  boxShadow: `0 0 6px ${colors.termAccent}80`,
                }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
