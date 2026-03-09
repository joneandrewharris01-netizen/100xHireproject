import { GoogleGenerativeAI } from "@google/generative-ai";
import type { AIProvider, GenerateResult } from "./provider";
import type { ContentMode } from "../../src/types/content";
import { getSystemPrompt, buildUserPrompt } from "./prompts";

export class GeminiProvider implements AIProvider {
  name = "gemini";
  private client: GoogleGenerativeAI;
  private model: string;

  constructor(apiKey: string, model?: string) {
    this.client = new GoogleGenerativeAI(apiKey);
    this.model = model || "gemini-2.0-flash";
  }

  async generateScript(
    prompt: string,
    mode: ContentMode,
    tone?: string,
    hooks: number = 3
  ): Promise<GenerateResult> {
    const systemPrompt = getSystemPrompt(mode);
    const userPrompt = buildUserPrompt(prompt, mode, tone, hooks);

    const model = this.client.getGenerativeModel({
      model: this.model,
      systemInstruction: systemPrompt,
    });

    const result = await model.generateContent(userPrompt);
    const response = result.response;
    const text = response.text();

    if (!text) {
      throw new Error("No text response from Gemini");
    }

    // Parse JSON from response (handle possible markdown wrapping)
    let jsonStr = text.trim();
    const fenceMatch = jsonStr.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (fenceMatch) {
      jsonStr = fenceMatch[1].trim();
    }

    const parsed = JSON.parse(jsonStr);

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
