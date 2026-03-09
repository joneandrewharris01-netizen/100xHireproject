import type { ContentMode, ContentScript } from "../../src/types/content";

export interface GenerateResult {
  title: string;
  hooks: string[];
  voiceoverScript: string;
  scenes: ContentScript["scenes"];
  cta: ContentScript["cta"];
}

export interface AIProvider {
  name: string;
  generateScript(
    prompt: string,
    mode: ContentMode,
    tone?: string,
    hooks?: number
  ): Promise<GenerateResult>;
}

export interface StudioConfig {
  aiProvider: "claude" | "gemini" | "openai" | "custom";
  apiKey: string;
  model: string;
  defaultVoice: string;
  defaultRate: string;
  defaultPitch: string;
}

export function getProvider(config: StudioConfig): AIProvider {
  switch (config.aiProvider) {
    case "gemini": {
      const { GeminiProvider } = require("./gemini");
      return new GeminiProvider(config.apiKey, config.model);
    }
    case "claude":
    default: {
      const { ClaudeProvider } = require("./claude");
      return new ClaudeProvider(config.apiKey, config.model);
    }
  }
}
