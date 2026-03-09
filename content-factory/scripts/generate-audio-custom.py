"""
TTS Pipeline with custom voice parameters.
Extended version of generate-audio.py that accepts CLI params for voice, rate, and pitch.

Usage:
  python generate-audio-custom.py --voice "en-US-JennyNeural" --rate "+20%" --pitch "+2Hz"

Falls back to mode defaults from existing VOICES dict if no params given.
"""

import sys
import os
import json
import asyncio
import argparse

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY_JSON = os.path.join(PROJECT_ROOT, "src", "data", "today.json")
AUDIO_DIR = os.path.join(PROJECT_ROOT, "public", "audio")
AUDIO_FILE = os.path.join(AUDIO_DIR, "voiceover.mp3")

# Voice settings per mode (fallback defaults)
VOICES = {
    "wealth": {"id": "en-US-GuyNeural", "rate": "+18%", "pitch": "+0Hz"},
    "apps": {"id": "en-US-AndrewNeural", "rate": "+15%", "pitch": "+0Hz"},
    "finance": {"id": "en-US-BrianNeural", "rate": "+10%", "pitch": "+0Hz"},
    "custom": {"id": "en-US-GuyNeural", "rate": "+15%", "pitch": "+0Hz"},
}


def get_voice_config(mode: str, args) -> dict:
    defaults = VOICES.get(mode, VOICES["custom"])
    return {
        "id": args.voice or defaults["id"],
        "rate": args.rate or defaults["rate"],
        "pitch": args.pitch or defaults["pitch"],
    }


async def generate_tts(text: str, output_path: str, voice_config: dict):
    """Generate TTS audio using edge-tts with custom voice settings."""
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
    parser = argparse.ArgumentParser(description="Generate TTS audio with custom voice params")
    parser.add_argument("--voice", type=str, default=None, help="Voice ID (e.g., en-US-JennyNeural)")
    parser.add_argument("--rate", type=str, default=None, help="Speech rate (e.g., +20%%)")
    parser.add_argument("--pitch", type=str, default=None, help="Voice pitch (e.g., +2Hz)")
    args = parser.parse_args()

    with open(TODAY_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    script = data["script"]["voiceoverScript"]
    mode = data["script"].get("mode", "wealth")
    print(f"[Pipeline] Mode: {mode}, Script length: {len(script)} chars")

    os.makedirs(AUDIO_DIR, exist_ok=True)

    # Step 1: Generate TTS with custom or mode-specific voice
    voice_config = get_voice_config(mode, args)
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
