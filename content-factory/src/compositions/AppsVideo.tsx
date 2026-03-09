import React from "react";
import { Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import type { ContentData } from "../types/content";
import { getTheme } from "../themes";
import { buildSectionsFromRatios } from "../utils/timing";
import { Background } from "../scenes/shared/Background";
import { WordCaptions } from "../scenes/shared/WordCaptions";
import { ProgressBar } from "../scenes/shared/ProgressBar";
import { AppsIntro } from "../scenes/apps/AppsIntro";
import { IdeaReveal } from "../scenes/apps/IdeaReveal";
import { SpeedBuild } from "../scenes/apps/SpeedBuild";
import { ResearchData } from "../scenes/apps/ResearchData";
import { AppsCTA } from "../scenes/apps/AppsCTA";
import { ToolShowcase } from "../scenes/shared/ToolShowcase";
import { APPS_BRAND } from "../data/brand-apps";

const OVERLAP = 10;

export const AppsVideo: React.FC<{ data: ContentData }> = ({ data }) => {
  const { durationInFrames } = useVideoConfig();
  const theme = getTheme("apps");

  const sceneNames = ["intro", "reveal", "build", "research", "cta"];
  const ratios = [0.18, 0.22, 0.22, 0.2, 0.18];
  const sections = buildSectionsFromRatios(sceneNames, ratios, durationInFrames);

  const getSection = (name: string) => sections.find((s) => s.name === name)!;

  const scenes = data.script.scenes;

  return (
    <div style={{ position: "relative", width: 1080, height: 1920, overflow: "hidden" }}>
      <Background theme={theme} />

      <Sequence from={getSection("intro").startFrame} durationInFrames={getSection("intro").durationFrames + OVERLAP} layout="none">
        <AppsIntro
          hook={data.script.hook}
          badge={APPS_BRAND.badge}
          appName={scenes[0]?.label}
          theme={theme}
          durationFrames={getSection("intro").durationFrames + OVERLAP}
        />
      </Sequence>

      {scenes[0] && (
        <Sequence from={getSection("reveal").startFrame} durationInFrames={getSection("reveal").durationFrames + OVERLAP} layout="none">
          {scenes[0].data?.toolImage ? (
            <ToolShowcase scene={scenes[0]} theme={theme} durationFrames={getSection("reveal").durationFrames + OVERLAP} />
          ) : (
            <IdeaReveal scene={scenes[0]} theme={theme} durationFrames={getSection("reveal").durationFrames + OVERLAP} />
          )}
        </Sequence>
      )}

      {scenes[1] && (
        <Sequence from={getSection("build").startFrame} durationInFrames={getSection("build").durationFrames + OVERLAP} layout="none">
          {scenes[1].data?.toolImage ? (
            <ToolShowcase scene={scenes[1]} theme={theme} durationFrames={getSection("build").durationFrames + OVERLAP} index={1} />
          ) : (
            <SpeedBuild scene={scenes[1]} theme={theme} durationFrames={getSection("build").durationFrames + OVERLAP} />
          )}
        </Sequence>
      )}

      {scenes[2] && (
        <Sequence from={getSection("research").startFrame} durationInFrames={getSection("research").durationFrames + OVERLAP} layout="none">
          {scenes[2].data?.toolImage ? (
            <ToolShowcase scene={scenes[2]} theme={theme} durationFrames={getSection("research").durationFrames + OVERLAP} index={2} />
          ) : (
            <ResearchData scene={scenes[2]} theme={theme} durationFrames={getSection("research").durationFrames + OVERLAP} />
          )}
        </Sequence>
      )}

      <Sequence from={getSection("cta").startFrame} layout="none">
        <AppsCTA
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
