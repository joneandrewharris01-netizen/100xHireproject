import React from "react";
import { Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import type { ContentData } from "../types/content";
import { getTheme } from "../themes";
import { buildSectionsFromRatios } from "../utils/timing";
import { ThreeBackground } from "../scenes/threed/ThreeBackground";
import { WordCaptions } from "../scenes/shared/WordCaptions";
import { ProgressBar } from "../scenes/shared/ProgressBar";
import { ThreeDIntro } from "../scenes/threed/ThreeDIntro";
import { ThreeDContent } from "../scenes/threed/ThreeDContent";
import { ThreeDCTA } from "../scenes/threed/ThreeDCTA";
import { THREED_BRAND } from "../data/brand-threed";

const OVERLAP = 10;

export const ThreeDVideo: React.FC<{ data: ContentData }> = ({ data }) => {
  const { durationInFrames } = useVideoConfig();
  const theme = getTheme("threed");

  const scenes = data.script.scenes;
  const contentCount = Math.min(scenes.length, 2);

  const sceneNames = ["intro"];
  const ratios = [0.2];

  if (contentCount >= 1) {
    sceneNames.push("content1");
    ratios.push(contentCount === 1 ? 0.55 : 0.3);
  }
  if (contentCount >= 2) {
    sceneNames.push("content2");
    ratios.push(0.25);
  }
  sceneNames.push("cta");
  ratios.push(0.2);

  const sum = ratios.reduce((a, b) => a + b, 0);
  const normalizedRatios = ratios.map((r) => r / sum);

  const sections = buildSectionsFromRatios(
    sceneNames,
    normalizedRatios,
    durationInFrames
  );
  const getSection = (name: string) => sections.find((s) => s.name === name)!;

  return (
    <div
      style={{
        position: "relative",
        width: 1080,
        height: 1920,
        overflow: "hidden",
      }}
    >
      <ThreeBackground theme={theme} />

      <Sequence
        from={getSection("intro").startFrame}
        durationInFrames={getSection("intro").durationFrames + OVERLAP}
        layout="none"
      >
        <ThreeDIntro
          hook={data.script.hook}
          badge={THREED_BRAND.badge}
          theme={theme}
          durationFrames={getSection("intro").durationFrames + OVERLAP}
        />
      </Sequence>

      {scenes[0] && sections.find((s) => s.name === "content1") && (
        <Sequence
          from={getSection("content1").startFrame}
          durationInFrames={getSection("content1").durationFrames + OVERLAP}
          layout="none"
        >
          <ThreeDContent
            scene={scenes[0]}
            theme={theme}
            durationFrames={getSection("content1").durationFrames + OVERLAP}
            sceneIndex={0}
          />
        </Sequence>
      )}

      {scenes[1] && sections.find((s) => s.name === "content2") && (
        <Sequence
          from={getSection("content2").startFrame}
          durationInFrames={getSection("content2").durationFrames + OVERLAP}
          layout="none"
        >
          <ThreeDContent
            scene={scenes[1]}
            theme={theme}
            durationFrames={getSection("content2").durationFrames + OVERLAP}
            sceneIndex={1}
          />
        </Sequence>
      )}

      <Sequence from={getSection("cta").startFrame} layout="none">
        <ThreeDCTA
          line1={data.script.cta.line1}
          line2={data.script.cta.line2}
          button={data.script.cta.button}
          theme={theme}
          durationFrames={durationInFrames - getSection("cta").startFrame}
        />
      </Sequence>

      <WordCaptions words={data.audio.words} theme={theme} />
      <ProgressBar theme={theme} />

      {data.audio.audioFile && (
        <Audio src={staticFile(data.audio.audioFile)} />
      )}
    </div>
  );
};
