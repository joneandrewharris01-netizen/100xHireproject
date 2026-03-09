# Content Factory — Remotion Video Engine

Multi-mode content video pipeline. 4 modes, distinct visual identities, unified architecture.

## Quick Reference

```bash
npm run dev                    # Remotion Studio (preview all 4 modes)
npm run render:wealth          # Full pipeline: pick → TTS → render wealth
npm run render:apps            # Full pipeline: pick → TTS → render apps
npm run render:finance         # Full pipeline: pick → TTS → render finance
npm run render:custom          # Render custom (requires content/custom/*.json)
npm run daily:all              # Render all 3 main modes
```

## Architecture

```
content/{mode}/*.json  →  pick-content.py  →  src/data/today.json
                                                      ↓
                                              generate-audio.py
                                                      ↓
                                            public/audio/voiceover.mp3
                                            (+ word timestamps in today.json)
                                                      ↓
                                          npx remotion render {CompositionId}
                                                      ↓
                                              out/{mode}/video.mp4
```

## 4 Modes

| Mode | Composition | Accent | Voice | Aesthetic |
|------|-------------|--------|-------|-----------|
| wealth | WealthVideo | #00D4FF cyan | en-US-GuyNeural | Hacker terminal |
| apps | AppsVideo | #22C55E green | en-US-AndrewNeural | Code editor |
| finance | FinanceVideo | #D4A843 gold | en-US-BrianNeural | Bloomberg |
| custom | CustomVideo | User-defined | User-defined | Full override |

## Design Rules (MUST follow)

- **Motion graphics must be present at ALL times** — no blank frames between scene transitions. Scenes use `<Sequence>` with OVERLAP crossfade (10 frames) so there is always something on screen.
- **Scene text/content must be vertically centered** (middle of the reel) on every mode. All scenes use `justifyContent: "center"` in their container.
- **WordCaptions sit at bottom** (top: 1420) — separate from the centered scene content.

## Key Patterns

- **Sequence + OVERLAP** — scenes crossfade via Remotion `<Sequence>` with 10-frame overlap, never `inSection()` guards
- **vis(frame, fps, enterAt, exitAt)** — animation visibility system
- **Spring presets** — FAST, SNAP, BOUNCY, SMOOTH in `src/utils/animations.ts`
- **AnimMode** — slamLeft/Right/Top/Bottom, zoomCenter, scaleUp
- **WordCaptions buildGroups()** — 2-3 word kinetic chunks
- **today.json bridge** — Python writes JSON, Remotion reads JSON
- **Theme system** — `getTheme(mode)` returns full ThemeConfig

## Content Script JSON Format

```json
{
  "id": "unique-id",
  "mode": "wealth|apps|finance|custom",
  "title": "Video Title",
  "hook": "Opening hook text",
  "voiceoverScript": "Full TTS script",
  "scenes": [
    {
      "id": "scene-id",
      "label": "Scene Title",
      "text": "Scene body text",
      "data": { "key": "value" }
    }
  ],
  "cta": { "line1": "CTA", "line2": "subtitle", "button": "button text" },
  "themeOverrides": {}
}
```

## Agent Workflow

Agents feed content INTO the pipeline (not into Remotion):
1. Agent generates ContentScript JSON
2. JSON saved to `content/{mode}/`
3. `npm run render:{mode}` runs the full pipeline

## Python Requirements

- Python: `C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe`
- edge-tts: `pip install edge-tts`
- faster-whisper: `pip install faster-whisper`

## Adding New Content

1. Create a JSON file in `content/{mode}/` following the format above
2. Run `npm run render:{mode}` — it picks a random script, generates TTS, renders video
3. Output lands in `out/{mode}/video.mp4`

## Custom Mode

Set `themeOverrides` in your JSON to customize colors, fonts, and badge:
```json
{
  "themeOverrides": {
    "badge": "My Brand",
    "colors": { "accent": "#FF6B9D", "accentLight": "#FF8FB3", "accentDark": "#E05580" }
  }
}
```
