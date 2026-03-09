import React from "react";
import { Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import type { ContentData } from "../types/content";
import { getTheme } from "../themes";
import { buildSectionsFromRatios } from "../utils/timing";
import { Background } from "../scenes/shared/Background";
import { WordCaptions } from "../scenes/shared/WordCaptions";
import { ProgressBar } from "../scenes/shared/ProgressBar";
import { FinanceIntro } from "../scenes/finance/FinanceIntro";
import { DataReveal } from "../scenes/finance/DataReveal";
import { GeographicScene } from "../scenes/finance/GeographicScene";
import { AIAnalysis } from "../scenes/finance/AIAnalysis";
import { FinanceCTA } from "../scenes/finance/FinanceCTA";
import { ToolShowcase } from "../scenes/shared/ToolShowcase";
import { FINANCE_BRAND } from "../data/brand-finance";

const OVERLAP = 10;

export const FinanceVideo: React.FC<{ data: ContentData }> = ({ data }) => {
  const { durationInFrames } = useVideoConfig();
  const theme = getTheme("finance");

  const sceneNames = ["intro", "data", "geo", "ai", "cta"];
  const ratios = [0.18, 0.22, 0.22, 0.2, 0.18];
  const sections = buildSectionsFromRatios(sceneNames, ratios, durationInFrames);

  const getSection = (name: string) => sections.find((s) => s.name === name)!;

  const scenes = data.script.scenes;
  const demographic = scenes[0]?.data?.demographic as string | undefined;

  return (
    <div style={{ position: "relative", width: 1080, height: 1920, overflow: "hidden" }}>
      <Background theme={theme} />

      <Sequence from={getSection("intro").startFrame} durationInFrames={getSection("intro").durationFrames + OVERLAP} layout="none">
        <FinanceIntro
          hook={data.script.hook}
          badge={FINANCE_BRAND.badge}
          demographic={demographic}
          theme={theme}
          durationFrames={getSection("intro").durationFrames + OVERLAP}
        />
      </Sequence>

      {scenes[0] && (
        <Sequence from={getSection("data").startFrame} durationInFrames={getSection("data").durationFrames + OVERLAP} layout="none">
          {scenes[0].data?.toolImage ? (
            <ToolShowcase scene={scenes[0]} theme={theme} durationFrames={getSection("data").durationFrames + OVERLAP} />
          ) : (
            <DataReveal scene={scenes[0]} theme={theme} durationFrames={getSection("data").durationFrames + OVERLAP} />
          )}
        </Sequence>
      )}

      {scenes[1] && (
        <Sequence from={getSection("geo").startFrame} durationInFrames={getSection("geo").durationFrames + OVERLAP} layout="none">
          {scenes[1].data?.toolImage ? (
            <ToolShowcase scene={scenes[1]} theme={theme} durationFrames={getSection("geo").durationFrames + OVERLAP} index={1} />
          ) : (
            <GeographicScene scene={scenes[1]} theme={theme} durationFrames={getSection("geo").durationFrames + OVERLAP} />
          )}
        </Sequence>
      )}

      {scenes[2] && (
        <Sequence from={getSection("ai").startFrame} durationInFrames={getSection("ai").durationFrames + OVERLAP} layout="none">
          {scenes[2].data?.toolImage ? (
            <ToolShowcase scene={scenes[2]} theme={theme} durationFrames={getSection("ai").durationFrames + OVERLAP} index={2} />
          ) : (
            <AIAnalysis scene={scenes[2]} theme={theme} durationFrames={getSection("ai").durationFrames + OVERLAP} />
          )}
        </Sequence>
      )}

      <Sequence from={getSection("cta").startFrame} layout="none">
        <FinanceCTA
          line1={data.script.cta.line1}
          line2={data.script.cta.line2}
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
