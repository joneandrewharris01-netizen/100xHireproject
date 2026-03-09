// Content mode identifier
export type ContentMode = "wealth" | "apps" | "finance" | "custom" | "threed";

// Word-level timestamp from Whisper
export interface WordTimestamp {
  word: string;
  start: number;
  end: number;
}

// Audio metadata from TTS + Whisper pipeline
export interface AudioMeta {
  audioFile: string;
  durationSeconds: number;
  words: WordTimestamp[];
}

// A single scene definition within a content script
export interface SceneDef {
  id: string;
  label: string;
  text: string;
  icon?: string;
  data?: Record<string, string | number>;
}

// Content script — the JSON that drives a single video
export interface ContentScript {
  id: string;
  mode: ContentMode;
  title: string;
  hook: string;
  voiceoverScript: string;
  scenes: SceneDef[];
  cta: {
    line1: string;
    line2?: string;
    button?: string;
  };
  // Optional overrides for custom mode
  themeOverrides?: Record<string, unknown>;
}

// The bridge JSON (today.json) that Remotion reads
export interface ContentData {
  script: ContentScript;
  audio: AudioMeta;
  generatedAt: string;
}

// Video section for timeline management
export interface VideoSection {
  name: string;
  startFrame: number;
  durationFrames: number;
}
