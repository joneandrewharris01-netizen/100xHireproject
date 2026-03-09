import fs from "fs";
import path from "path";
import type { StudioConfig } from "./ai/provider";

const CONFIG_FILE = path.join("D:", "Projects", "my-project", "content-factory", "studio-config.json");

const DEFAULT_CONFIG: StudioConfig = {
  aiProvider: "claude",
  apiKey: "",
  model: "claude-sonnet-4-6",
  defaultVoice: "en-US-GuyNeural",
  defaultRate: "+15%",
  defaultPitch: "+0Hz",
};

export function readConfig(): StudioConfig {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      const raw = fs.readFileSync(CONFIG_FILE, "utf-8");
      return { ...DEFAULT_CONFIG, ...JSON.parse(raw) };
    }
  } catch {
    // Fall through to default
  }
  return { ...DEFAULT_CONFIG };
}

export function writeConfig(config: Partial<StudioConfig>): StudioConfig {
  const current = readConfig();
  const merged = { ...current, ...config };
  fs.writeFileSync(CONFIG_FILE, JSON.stringify(merged, null, 2), "utf-8");
  return merged;
}

export function getApiKey(): string {
  // Prefer environment variable, fall back to config file
  return process.env.ANTHROPIC_API_KEY || readConfig().apiKey;
}
