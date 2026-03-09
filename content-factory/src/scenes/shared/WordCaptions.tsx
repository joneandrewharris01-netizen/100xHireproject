import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import type { ThemeConfig } from "../../types/themes";
import type { WordTimestamp } from "../../types/content";
import { SNAP, SLIDE_CYCLE, getSlideTransform } from "../../utils/animations";

interface WordGroup {
  words: WordTimestamp[];
  text: string;
  start: number;
  end: number;
}

function buildGroups(words: WordTimestamp[]): WordGroup[] {
  const groups: WordGroup[] = [];
  let current: WordTimestamp[] = [];

  for (let i = 0; i < words.length; i++) {
    current.push(words[i]);

    const isEnd =
      current.length >= 3 ||
      i === words.length - 1 ||
      (i < words.length - 1 && words[i + 1].start - words[i].end > 0.12) ||
      /[.!?]$/.test(words[i].word);

    if (isEnd) {
      groups.push({
        words: [...current],
        text: current.map((w) => w.word).join(" "),
        start: current[0].start,
        end: current[current.length - 1].end,
      });
      current = [];
    }
  }

  return groups;
}

const EXIT_FRAMES = 6;

export const WordCaptions: React.FC<{
  words: WordTimestamp[];
  theme: ThemeConfig;
}> = ({ words, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { captions } = theme;
  const time = frame / fps;

  const groups = buildGroups(words);

  // Find active group
  const activeIdx = groups.findIndex((g) => time >= g.start && time <= g.end + 0.15);
  if (activeIdx < 0) return null;

  const group = groups[activeIdx];
  const slideDir = SLIDE_CYCLE[activeIdx % SLIDE_CYCLE.length];
  const groupStartFrame = Math.round(group.start * fps);
  const enterProgress = spring({
    frame: frame - groupStartFrame,
    fps,
    config: SNAP,
  });

  return (
    <div
      style={{
        position: "absolute",
        top: captions.top,
        left: 40,
        right: 40,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        gap: 14,
        transform: getSlideTransform(slideDir, enterProgress),
        opacity: enterProgress,
      }}
    >
      {/* Backdrop */}
      <div
        style={{
          position: "absolute",
          inset: -16,
          background: "rgba(0, 0, 0, 0.5)",
          borderRadius: 16,
          zIndex: -1,
        }}
      />
      {group.words.map((w, i) => {
        const wordTime = w.start;
        const isActive = time >= wordTime && time <= w.end;
        const wordFrame = Math.round(wordTime * fps);
        const pop = spring({
          frame: frame - wordFrame,
          fps,
          config: SNAP,
        });

        return (
          <span
            key={`${activeIdx}-${i}`}
            style={{
              fontSize: isActive ? captions.activeFontSize : captions.fontSize,
              fontWeight: 800,
              fontFamily: theme.fonts.heading,
              color: isActive ? captions.activeColor : captions.inactiveColor,
              textShadow: isActive
                ? `0 0 20px ${captions.glowColor}, 0 0 40px ${captions.glowColor}`
                : "0 2px 8px rgba(0,0,0,0.5)",
              transform: isActive ? `scale(${0.9 + 0.1 * pop})` : "scale(1)",
              transition: "font-size 0.1s, color 0.1s",
              textTransform: "uppercase",
            }}
          >
            {w.word}
          </span>
        );
      })}
    </div>
  );
};
