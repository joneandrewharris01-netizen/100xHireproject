import type { VideoSection } from "../types/content";

const FPS = 30;

export function secondsToFrames(seconds: number): number {
  return Math.round(seconds * FPS);
}

export function framesToSeconds(frames: number): number {
  return frames / FPS;
}

// Get total frames — minimum 15s, pad 1s after audio ends
export function getTotalFrames(durationSeconds: number): number {
  const minDuration = Math.max(durationSeconds + 1, 15);
  return secondsToFrames(minDuration);
}

// Build evenly-spaced sections for a given number of scenes
export function buildSections(
  sceneNames: string[],
  totalFrames: number
): VideoSection[] {
  const count = sceneNames.length;
  const perScene = Math.floor(totalFrames / count);
  const sections: VideoSection[] = [];

  for (let i = 0; i < count; i++) {
    sections.push({
      name: sceneNames[i],
      startFrame: i * perScene,
      durationFrames: i === count - 1 ? totalFrames - i * perScene : perScene,
    });
  }

  return sections;
}

// Build sections from percentage-based timing
export function buildSectionsFromRatios(
  sceneNames: string[],
  ratios: number[],
  totalFrames: number
): VideoSection[] {
  const sections: VideoSection[] = [];
  let currentFrame = 0;

  for (let i = 0; i < sceneNames.length; i++) {
    const duration =
      i === sceneNames.length - 1
        ? totalFrames - currentFrame
        : Math.round(totalFrames * ratios[i]);
    sections.push({
      name: sceneNames[i],
      startFrame: currentFrame,
      durationFrames: duration,
    });
    currentFrame += duration;
  }

  return sections;
}

// Get which section the current frame is in
export function getCurrentSection(
  frame: number,
  sections: VideoSection[]
): VideoSection | null {
  for (const s of sections) {
    if (frame >= s.startFrame && frame < s.startFrame + s.durationFrames) {
      return s;
    }
  }
  return sections[sections.length - 1] || null;
}

// Check if voice is speaking at a given frame
export function getIsSpeaking(
  frame: number,
  words: { start: number; end: number }[]
): boolean {
  const t = framesToSeconds(frame);
  return words.some((w) => t >= w.start && t <= w.end);
}
