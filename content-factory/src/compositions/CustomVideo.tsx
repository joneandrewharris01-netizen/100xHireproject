import React from "react";
import { Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import type { ContentData } from "../types/content";
import { getTheme } from "../themes";
import { buildSectionsFromRatios } from "../utils/timing";
import { Background } from "../scenes/shared/Background";
import { WordCaptions } from "../scenes/shared/WordCaptions";
import { ProgressBar } from "../scenes/shared/ProgressBar";
import { CustomIntro } from "../scenes/custom/CustomIntro";
import { ContentScene } from "../scenes/custom/ContentScene";
import { CustomCTA } from "../scenes/custom/CustomCTA";
import { ToolShowcase } from "../scenes/shared/ToolShowcase";

const OVERLAP = 10;

export const CustomVideo: React.FC<{ data: ContentData }> = ({ data }) => {
  const { durationInFrames } = useVideoConfig();

  const theme = getTheme(
    "custom",
    (data.script.themeOverrides as Record<string, unknown>) || {}
  );

  const contentScenes = data.script.scenes;
  const sceneNames = [
    "intro",
    ...contentScenes.map((_, i) => `content-${i}`),
    "cta",
  ];
  const totalScenes = sceneNames.length;
  const ratios = sceneNames.map((_, i) => {
    if (i === 0) return 0.2;
    if (i === totalScenes - 1) return 0.2;
    return 0.6 / contentScenes.length;
  });
  const sections = buildSectionsFromRatios(sceneNames, ratios, durationInFrames);

  const getSection = (name: string) => sections.find((s) => s.name === name)!;

  const badge = String(
    (data.script.themeOverrides as Record<string, unknown>)?.badge ||
      data.script.title ||
      "Custom"
  );

  return (
    <div style={{ position: "relative", width: 1080, height: 1920, overflow: "hidden" }}>
      <Background theme={theme} />

      <Sequence from={getSection("intro").startFrame} durationInFrames={getSection("intro").durationFrames + OVERLAP} layout="none">
        <CustomIntro
          hook={data.script.hook}
          badge={badge}
          theme={theme}
          durationFrames={getSection("intro").durationFrames + OVERLAP}
        />
      </Sequence>

      {contentScenes.map((scene, i) => {
        const name = `content-${i}`;
        const sec = getSection(name);
        const isLast = i === contentScenes.length - 1;
        return (
          <Sequence key={name} from={sec.startFrame} durationInFrames={sec.durationFrames + OVERLAP} layout="none">
            {scene.data?.toolImage ? (
              <ToolShowcase scene={scene} theme={theme} durationFrames={sec.durationFrames + OVERLAP} index={i} />
            ) : (
              <ContentScene scene={scene} theme={theme} durationFrames={sec.durationFrames + OVERLAP} index={i} />
            )}
          </Sequence>
        );
      })}

      <Sequence from={getSection("cta").startFrame} layout="none">
        <CustomCTA
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
