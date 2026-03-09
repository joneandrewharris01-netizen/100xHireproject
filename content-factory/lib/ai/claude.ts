import Anthropic from "@anthropic-ai/sdk";
import type { AIProvider, GenerateResult } from "./provider";
import type { ContentMode } from "../../src/types/content";
import { getSystemPrompt, buildUserPrompt } from "./prompts";

export class ClaudeProvider implements AIProvider {
  name = "claude";
  private client: Anthropic;
  private model: string;

  constructor(apiKey: string, model?: string) {
    this.client = new Anthropic({ apiKey });
    this.model = model || "claude-sonnet-4-6";
  }

  async generateScript(
    prompt: string,
    mode: ContentMode,
    tone?: string,
    hooks: number = 3
  ): Promise<GenerateResult> {
    const systemPrompt = getSystemPrompt(mode);
    const userPrompt = buildUserPrompt(prompt, mode, tone, hooks);

    const response = await this.client.messages.create({
      model: this.model,
      max_tokens: 2048,
      system: systemPrompt,
      messages: [{ role: "user", content: userPrompt }],
    });

    // Extract text from response
    const textBlock = response.content.find((b) => b.type === "text");
    if (!textBlock || textBlock.type !== "text") {
      throw new Error("No text response from Claude");
    }

    // Parse JSON from response (handle possible markdown wrapping)
    let jsonStr = textBlock.text.trim();
    const fenceMatch = jsonStr.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (fenceMatch) {
      jsonStr = fenceMatch[1].trim();
    }

    const parsed = JSON.parse(jsonStr);

    // Validate required fields
    if (!parsed.title || !parsed.hooks || !parsed.voiceoverScript || !parsed.scenes || !parsed.cta) {
      throw new Error("AI response missing required fields");
    }

    return {
      title: parsed.title,
      hooks: Array.isArray(parsed.hooks) ? parsed.hooks : [parsed.hooks],
      voiceoverScript: parsed.voiceoverScript,
      scenes: parsed.scenes,
      cta: parsed.cta,
    };
  }
}
