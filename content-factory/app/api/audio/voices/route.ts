import { NextResponse } from "next/server";
import { execSync } from "child_process";

interface VoiceInfo {
  id: string;
  name: string;
  gender: string;
  locale: string;
}

let cachedVoices: VoiceInfo[] | null = null;

export async function GET() {
  try {
    if (cachedVoices) {
      return NextResponse.json(cachedVoices);
    }

    const PYTHON = "C:\\Users\\Admin\\AppData\\Local\\Programs\\Python\\Python311\\python.exe";
    const raw = execSync(
      `"${PYTHON}" -m edge_tts --list-voices`,
      { encoding: "utf-8", timeout: 30000 }
    );

    const voices: VoiceInfo[] = [];
    let current: Partial<VoiceInfo> = {};

    for (const line of raw.split("\n")) {
      const trimmed = line.trim();
      if (trimmed.startsWith("Name: ")) {
        if (current.id) voices.push(current as VoiceInfo);
        const fullName = trimmed.slice(6);
        current = {
          id: fullName,
          name: fullName.split("-").pop()?.replace("Neural", "") || fullName,
          locale: fullName.split("-").slice(0, 2).join("-"),
        };
      } else if (trimmed.startsWith("Gender: ")) {
        current.gender = trimmed.slice(8);
      }
    }
    if (current.id) voices.push(current as VoiceInfo);

    // Filter to English voices for usability
    const englishVoices = voices.filter((v) => v.locale.startsWith("en-"));

    cachedVoices = englishVoices;
    return NextResponse.json(englishVoices);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Failed to list voices";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
