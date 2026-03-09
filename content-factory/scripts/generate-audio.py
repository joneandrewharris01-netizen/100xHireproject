"""
TTS Pipeline: Generates voiceover audio from today.json and adds word timestamps.
Uses edge-tts for speech synthesis and faster-whisper for word-level alignment.

Supports per-mode voice selection:
  wealth  → en-US-GuyNeural (deep, authoritative)
  apps    → en-US-AndrewNeural (warm, builder)
  finance → en-US-BrianNeural (measured, credible)
  custom  → user-defined or default Guy

Usage:
  python generate-audio.py
"""

import sys
import os
import json
import asyncio

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY_JSON = os.path.join(PROJECT_ROOT, "src", "data", "today.json")
AUDIO_DIR = os.path.join(PROJECT_ROOT, "public", "audio")
AUDIO_FILE = os.path.join(AUDIO_DIR, "voiceover.mp3")

# Voice settings per mode
VOICES = {
    "wealth": {
        "id": "en-US-GuyNeural",
        "rate": "+18%",
        "pitch": "+0Hz",
    },
    "apps": {
        "id": "en-US-AndrewNeural",
        "rate": "+15%",
        "pitch": "+0Hz",
    },
    "finance": {
        "id": "en-US-BrianNeural",
        "rate": "+10%",
        "pitch": "+0Hz",
    },
    "custom": {
        "id": "en-US-GuyNeural",
        "rate": "+15%",
        "pitch": "+0Hz",
    },
    "threed": {
        "id": "en-US-GuyNeural",
        "rate": "+15%",
        "pitch": "+0Hz",
    },
}


def get_voice_config(mode: str) -> dict:
    return VOICES.get(mode, VOICES["custom"])


async def generate_tts(text: str, output_path: str, voice_config: dict):
    """Generate TTS audio using edge-tts with per-mode voice settings."""
    import edge_tts

    communicate = edge_tts.Communicate(
        text,
        voice_config["id"],
        rate=voice_config["rate"],
        pitch=voice_config["pitch"],
    )
    await communicate.save(output_path)
    print(f"[TTS] Voice: {voice_config['id']} (rate={voice_config['rate']}, pitch={voice_config['pitch']})")
    print(f"[TTS] Audio saved to {output_path}")


def transcribe_with_timestamps(audio_path: str) -> tuple:
    """Transcribe audio and extract word-level timestamps using faster-whisper."""
    from faster_whisper import WhisperModel

    print("[Whisper] Loading model (base)...")
    model = WhisperModel("base", device="cpu", compute_type="int8")

    print("[Whisper] Transcribing...")
    segments, info = model.transcribe(audio_path, word_timestamps=True)

    words = []
    for segment in segments:
        if segment.words:
            for w in segment.words:
                words.append({
                    "word": w.word.strip(),
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                })

    duration = info.duration
    print(f"[Whisper] Duration: {duration:.2f}s, Words: {len(words)}")
    return duration, words


def main():
    with open(TODAY_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    script = data["script"]["voiceoverScript"]
    mode = data["script"].get("mode", "wealth")
    print(f"[Pipeline] Mode: {mode}, Script length: {len(script)} chars")

    os.makedirs(AUDIO_DIR, exist_ok=True)

    # Step 1: Generate TTS with mode-specific voice
    voice_config = get_voice_config(mode)
    asyncio.run(generate_tts(script, AUDIO_FILE, voice_config))

    # Step 2: Transcribe for word timestamps
    duration, words = transcribe_with_timestamps(AUDIO_FILE)

    # Step 3: Update today.json
    data["audio"]["audioFile"] = "audio/voiceover.mp3"
    data["audio"]["durationSeconds"] = round(duration, 2)
    data["audio"]["words"] = words

    with open(TODAY_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[Pipeline] Updated today.json with {len(words)} word timestamps")
    print("[Pipeline] Done!")


if __name__ == "__main__":
    main()
