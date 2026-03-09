import React from "react";
import { Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import type { ContentData } from "../types/content";
import { getTheme } from "../themes";
import { Background } from "../scenes/shared/Background";
import { WordCaptions } from "../scenes/shared/WordCaptions";
import { ProgressBar } from "../scenes/shared/ProgressBar";
import { WealthIntro } from "../scenes/wealth/WealthIntro";
import { ClientStory } from "../scenes/wealth/ClientStory";
import { MoneyReveal } from "../scenes/wealth/MoneyReveal";
import { WealthCTA } from "../scenes/wealth/WealthCTA";
import { ToolShowcase } from "../scenes/shared/ToolShowcase";
import { WEALTH_BRAND } from "../data/brand-wealth";

const OVERLAP = 10; // crossfade frames between scenes
const FPS = 30;

/**
 * Map voiceover keywords to scene start times (seconds).
 * Falls back to evenly-split timing if words are missing.
 */
function findWordTime(
  words: { word: string; start: number; end: number }[],
  keywords: string[]
): number | null {
  for (const kw of keywords) {
    const w = words.find(
      (wd) => wd.word.toLowerCase().replace(/[.,!?]/g, "") === kw.toLowerCase()
    );
    if (w) return w.start;
  }
  return null;
}

function buildVoiceSyncedSections(
  sceneCount: number,
  words: { word: string; start: number; end: number }[],
  totalFrames: number
) {
  // Try to find voiceover cue points for each tool
  const cueKeywords = [
    ["first", "n8n"],
    ["second", "make"],
    ["third", "zapier"],
    ["fourth", "claude"],
    ["fifth", "airtable"],
  ];
  const ctaKeywords = ["save"];

  // Intro: 0 -> first tool mention
  const firstToolTime = findWordTime(words, [cueKeywords[0][0]]);
  const introEnd = firstToolTime ? Math.round(firstToolTime * FPS) : Math.round(totalFrames * 0.1);

  // CTA: "Save this list"
  const ctaTime = findWordTime(words, ctaKeywords);
  const ctaStart = ctaTime
    ? Math.round((ctaTime - 0.5) * FPS) // slight lead-in
    : totalFrames - Math.round(totalFrames * 0.08);

  // Tool scenes fill the space between intro and CTA
  const toolZoneStart = introEnd;
  const toolZoneEnd = ctaStart;
  const toolZoneFrames = toolZoneEnd - toolZoneStart;

  // Try voice-synced boundaries for each tool
  const toolStarts: number[] = [];
  for (let i = 0; i < sceneCount; i++) {
    if (i < cueKeywords.length) {
      const t = findWordTime(words, [cueKeywords[i][0]]);
      if (t !== null) {
        // Start scene ~0.3s before the cue word for smooth transition
        toolStarts.push(Math.max(toolZoneStart, Math.round((t - 0.3) * FPS)));
        continue;
      }
    }
    // Fallback: evenly divide
    toolStarts.push(toolZoneStart + Math.round((i / sceneCount) * toolZoneFrames));
  }

  const sections: { startFrame: number; durationFrames: number }[] = [];

  // Intro
  sections.push({ startFrame: 0, durationFrames: introEnd });

  // Tool scenes
  for (let i = 0; i < sceneCount; i++) {
    const start = toolStarts[i];
    const end = i < sceneCount - 1 ? toolStarts[i + 1] : ctaStart;
    sections.push({ startFrame: start, durationFrames: end - start });
  }

  // CTA
  sections.push({ startFrame: ctaStart, durationFrames: totalFrames - ctaStart });

  return sections;
}

export const WealthVideo: React.FC<{ data: ContentData }> = ({ data }) => {
  const { durationInFrames } = useVideoConfig();
  const theme = getTheme("wealth");

  const scenes = data.script.scenes;
  const hasToolShowcase = scenes.some((s) => s.data?.toolVideo || s.data?.toolImage);

  // Voice-synced sections: [intro, ...tools, cta]
  const sections = hasToolShowcase
    ? buildVoiceSyncedSections(scenes.length, data.audio.words, durationInFrames)
    : null;

  // Fallback: legacy 4-section layout for non-tool-showcase content
  if (!sections) {
    const { buildSectionsFromRatios } = require("../utils/timing");
    const sceneNames = ["intro", "story", "money", "cta"];
    const ratios = [0.2, 0.35, 0.25, 0.2];
    const legacySections = buildSectionsFromRatios(sceneNames, ratios, durationInFrames);
    const getSection = (name: string) => legacySections.find((s: any) => s.name === name)!;

    return (
      <div style={{ position: "relative", width: 1080, height: 1920, overflow: "hidden" }}>
        <Background theme={theme} />

        <Sequence from={getSection("intro").startFrame} durationInFrames={getSection("intro").durationFrames + OVERLAP} layout="none">
          <WealthIntro hook={data.script.hook} badge={WEALTH_BRAND.badge} theme={theme} durationFrames={getSection("intro").durationFrames + OVERLAP} />
        </Sequence>

        {scenes[0] && (
          <Sequence from={getSection("story").startFrame} durationInFrames={getSection("story").durationFrames + OVERLAP} layout="none">
            <ClientStory scene={scenes[0]} theme={theme} durationFrames={getSection("story").durationFrames + OVERLAP} />
          </Sequence>
        )}

        {scenes[1] && (
          <Sequence from={getSection("money").startFrame} durationInFrames={getSection("money").durationFrames + OVERLAP} layout="none">
            <MoneyReveal scene={scenes[1]} theme={theme} durationFrames={getSection("money").durationFrames + OVERLAP} />
          </Sequence>
        )}

        <Sequence from={getSection("cta").startFrame} layout="none">
          <WealthCTA line1={data.script.cta.line1} line2={data.script.cta.line2} button={data.script.cta.button} theme={theme} durationFrames={durationInFrames - getSection("cta").startFrame} />
        </Sequence>

        <WordCaptions words={data.audio.words} theme={theme} />
        <ProgressBar theme={theme} />
        {data.audio.audioFile && <Audio src={staticFile(data.audio.audioFile)} />}
      </div>
    );
  }

  // Tool showcase layout: intro + N tools + CTA, all voice-synced
  const introSec = sections[0];
  const ctaSec = sections[sections.length - 1];
  const toolSections = sections.slice(1, -1);

  return (
    <div style={{ position: "relative", width: 1080, height: 1920, overflow: "hidden" }}>
      <Background theme={theme} />

      {/* Intro */}
      <Sequence from={introSec.startFrame} durationInFrames={introSec.durationFrames + OVERLAP} layout="none">
        <WealthIntro
          hook={data.script.hook}
          badge={WEALTH_BRAND.badge}
          theme={theme}
          durationFrames={introSec.durationFrames + OVERLAP}
        />
      </Sequence>

      {/* Tool scenes — one per tool, voice-synced */}
      {scenes.map((scene, i) => {
        if (i >= toolSections.length) return null;
        const sec = toolSections[i];
        return (
          <Sequence
            key={scene.id}
            from={sec.startFrame}
            durationInFrames={sec.durationFrames + OVERLAP}
            layout="none"
          >
            <ToolShowcase
              scene={scene}
              theme={theme}
              durationFrames={sec.durationFrames + OVERLAP}
              index={i}
            />
          </Sequence>
        );
      })}

      {/* CTA */}
      <Sequence from={ctaSec.startFrame} layout="none">
        <WealthCTA
          line1={data.script.cta.line1}
          line2={data.script.cta.line2}
          button={data.script.cta.button}
          theme={theme}
          durationFrames={durationInFrames - ctaSec.startFrame}
        />
      </Sequence>

      <WordCaptions words={data.audio.words} theme={theme} />
      <ProgressBar theme={theme} />
      {data.audio.audioFile && <Audio src={staticFile(data.audio.audioFile)} />}
    </div>
  );
};
