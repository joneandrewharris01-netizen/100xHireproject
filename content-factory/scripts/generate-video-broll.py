"""
Generate AI video b-roll for tool showcase reels.

Supports multiple FREE methods:
1. Playwright screen recordings (navigate real websites)
2. fal.ai API (free credits - Hailuo, Kling, etc.)
3. Replicate API (free tier - no credit card)

Usage:
  python generate-video-broll.py                   # All methods
  python generate-video-broll.py --method screen    # Screen recordings only
  python generate-video-broll.py --method ai        # AI video gen only
  python generate-video-broll.py --tool n8n         # Specific tool only
"""
import sys
import os
import argparse
import json
import time
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

FFMPEG = r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "tools")

# Tool configurations
TOOLS = {
    "n8n": {
        "name": "n8n",
        "url": "https://n8n.io",
        "ai_prompt": "A sleek dark-themed workflow automation dashboard showing connected API nodes with glowing data flowing between them, professional UI design, 4K quality, smooth animation",
        "scroll_steps": [
            {"action": "goto", "url": "https://n8n.io", "wait": 3},
            {"action": "dismiss_cookies"},
            {"action": "wait", "seconds": 1},
            {"action": "scroll", "y": 400, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 600, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 400, "speed": "slow"},
            {"action": "wait", "seconds": 1},
            {"action": "scroll", "y": 300, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": -1000, "speed": "slow"},
            {"action": "wait", "seconds": 2},
        ],
    },
    "make": {
        "name": "Make.com",
        "url": "https://www.make.com/en",
        "ai_prompt": "A colorful visual automation builder interface with purple gradient background, connected circular nodes showing data flow between apps like Gmail, Slack, and Sheets, professional SaaS UI, smooth camera movement",
        "scroll_steps": [
            {"action": "goto", "url": "https://www.make.com/en", "wait": 5},
            {"action": "dismiss_cookies"},
            {"action": "wait", "seconds": 1},
            {"action": "scroll", "y": 500, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 500, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 400, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": -800, "speed": "slow"},
            {"action": "wait", "seconds": 2},
        ],
    },
    "zapier": {
        "name": "Zapier",
        "url": "https://zapier.com",
        "ai_prompt": "A clean automation platform interface showing Zap workflow connections between apps with orange accent colors, professional dashboard view, smooth scrolling animation",
        "scroll_steps": [
            {"action": "goto", "url": "https://zapier.com", "wait": 4},
            {"action": "dismiss_cookies"},
            {"action": "wait", "seconds": 1},
            {"action": "scroll", "y": 400, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 500, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 400, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": -800, "speed": "slow"},
            {"action": "wait", "seconds": 2},
        ],
    },
    "claude": {
        "name": "Claude",
        "url": "https://claude.ai",
        "ai_prompt": "A modern AI chat interface showing an intelligent assistant responding to a complex question with formatted text, code blocks, and analysis, warm beige background, professional UI, smooth typing animation",
        "scroll_steps": [
            {"action": "goto", "url": "https://claude.ai", "wait": 4},
            {"action": "dismiss_cookies"},
            {"action": "wait", "seconds": 3},
            {"action": "scroll", "y": 300, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 300, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": -400, "speed": "slow"},
            {"action": "wait", "seconds": 2},
        ],
    },
    "airtable": {
        "name": "Airtable",
        "url": "https://airtable.com",
        "ai_prompt": "A powerful spreadsheet database interface with colorful rows, kanban board view, and connected automation pipelines, blue accent theme, professional data management UI, smooth transitions",
        "scroll_steps": [
            {"action": "goto", "url": "https://airtable.com", "wait": 4},
            {"action": "dismiss_cookies"},
            {"action": "wait", "seconds": 1},
            {"action": "scroll", "y": 400, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 500, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 400, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": -800, "speed": "slow"},
            {"action": "wait", "seconds": 2},
        ],
    },
}


# ─── METHOD 1: Screen Recordings via Playwright ───

def smooth_scroll(page, y_delta, duration_ms=1500):
    steps = 30
    step_delay = duration_ms / steps
    step_y = y_delta / steps
    for _ in range(steps):
        page.evaluate(f"window.scrollBy(0, {step_y})")
        page.wait_for_timeout(int(step_delay))


def dismiss_cookies(page):
    page.evaluate("""
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            const txt = b.textContent.trim().toLowerCase();
            if (txt.includes('accept') || txt === 'understood' || txt === 'got it' || txt === 'ok') {
                b.click(); break;
            }
        }
    """)
    page.wait_for_timeout(1000)
    page.evaluate("""
        document.querySelectorAll('[class*=cookie],[id*=cookie],[class*=consent]')
            .forEach(el => el.style.display = 'none');
        document.querySelectorAll('[aria-label="Close"],[aria-label="close"],button[class*=close]')
            .forEach(b => { try { b.click(); } catch(e) {} });
    """)
    page.wait_for_timeout(500)


def record_screen(tool_key, tool_config):
    """Record a screen demo of a tool's website."""
    from playwright.sync_api import sync_playwright

    output_webm = os.path.join(OUTPUT_DIR, f"{tool_key}-demo.webm")
    output_mp4 = os.path.join(OUTPUT_DIR, f"{tool_key}-demo-trimmed.mp4")

    print(f"  [Screen] Recording {tool_config['name']}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 720},
            device_scale_factor=1,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1280, "height": 720},
        )

        page = ctx.new_page()

        for step in tool_config["scroll_steps"]:
            action = step["action"]
            try:
                if action == "goto":
                    page.goto(step["url"], wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(step.get("wait", 3) * 1000)
                elif action == "dismiss_cookies":
                    dismiss_cookies(page)
                elif action == "wait":
                    page.wait_for_timeout(step["seconds"] * 1000)
                elif action == "scroll":
                    smooth_scroll(page, step["y"])
                elif action == "hover":
                    try:
                        page.locator(step["selector"]).first.hover(timeout=2000)
                    except: pass
                elif action == "click":
                    try:
                        page.locator(step["selector"]).first.click(timeout=2000)
                    except: pass
            except Exception as e:
                print(f"    Step error ({action}): {e}")

        page.close()
        ctx.close()
        browser.close()

    # Find and rename the latest webm
    import glob
    webm_files = sorted(
        glob.glob(os.path.join(OUTPUT_DIR, "*.webm")),
        key=os.path.getmtime, reverse=True,
    )
    if webm_files:
        latest = webm_files[0]
        if os.path.abspath(latest) != os.path.abspath(output_webm):
            if os.path.exists(output_webm):
                os.remove(output_webm)
            os.rename(latest, output_webm)

    # Convert to mp4 and trim loading time
    if os.path.exists(output_webm):
        subprocess.run([
            FFMPEG, "-y", "-ss", "3", "-i", output_webm,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p", output_mp4,
        ], capture_output=True)
        size_kb = os.path.getsize(output_mp4) / 1024
        print(f"  [Screen] Saved: {output_mp4} ({size_kb:.0f} KB)")
        return output_mp4

    return None


# ─── METHOD 2: AI Video Generation via fal.ai ───

def generate_ai_video(tool_key, tool_config):
    """Generate AI video b-roll using fal.ai free tier."""
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        print("  [AI] Skipping — FAL_KEY not set. Get free key at https://fal.ai/dashboard/keys")
        return None

    try:
        import fal_client
    except ImportError:
        print("  [AI] Skipping — fal-client not installed. Run: pip install fal-client")
        return None

    output_mp4 = os.path.join(OUTPUT_DIR, f"{tool_key}-ai-broll.mp4")
    prompt = tool_config["ai_prompt"]

    print(f"  [AI] Generating video for {tool_config['name']}...")
    print(f"  [AI] Prompt: {prompt[:80]}...")

    try:
        # Use MiniMax Hailuo (good quality, has free credits on fal.ai)
        result = fal_client.subscribe(
            "fal-ai/minimax/video/01/live",
            arguments={
                "prompt": prompt,
                "prompt_optimizer": True,
            },
        )

        video_url = result.get("video", {}).get("url")
        if video_url:
            # Download the video
            import urllib.request
            urllib.request.urlretrieve(video_url, output_mp4)
            size_kb = os.path.getsize(output_mp4) / 1024
            print(f"  [AI] Saved: {output_mp4} ({size_kb:.0f} KB)")
            return output_mp4
        else:
            print(f"  [AI] No video URL in response: {result}")
    except Exception as e:
        print(f"  [AI] Error: {e}")

    return None


# ─── METHOD 3: Replicate free tier ───

def generate_replicate_video(tool_key, tool_config):
    """Generate AI video using Replicate's free tier."""
    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    if not replicate_token:
        print("  [Replicate] Skipping — REPLICATE_API_TOKEN not set. Get free at https://replicate.com")
        return None

    try:
        import replicate
    except ImportError:
        print("  [Replicate] Skipping — replicate not installed. Run: pip install replicate")
        return None

    output_mp4 = os.path.join(OUTPUT_DIR, f"{tool_key}-replicate-broll.mp4")
    prompt = tool_config["ai_prompt"]

    print(f"  [Replicate] Generating video for {tool_config['name']}...")

    try:
        output = replicate.run(
            "minimax/video-01-live",
            input={"prompt": prompt, "prompt_optimizer": True},
        )
        if output:
            import urllib.request
            video_url = str(output)
            urllib.request.urlretrieve(video_url, output_mp4)
            size_kb = os.path.getsize(output_mp4) / 1024
            print(f"  [Replicate] Saved: {output_mp4} ({size_kb:.0f} KB)")
            return output_mp4
    except Exception as e:
        print(f"  [Replicate] Error: {e}")

    return None


# ─── Main ───

def main():
    parser = argparse.ArgumentParser(description="Generate video b-roll for tool showcase reels")
    parser.add_argument("--method", choices=["screen", "ai", "replicate", "all"], default="all")
    parser.add_argument("--tool", help="Generate for specific tool only (e.g., n8n, make, zapier)")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    tools_to_process = {args.tool: TOOLS[args.tool]} if args.tool else TOOLS

    results = {}

    for key, config in tools_to_process.items():
        print(f"\n{'='*50}")
        print(f"Processing: {config['name']}")
        print(f"{'='*50}")

        tool_results = {}

        # Screen recording (always free, no API key needed)
        if args.method in ("screen", "all"):
            path = record_screen(key, config)
            if path:
                tool_results["screen"] = path

        # fal.ai AI video
        if args.method in ("ai", "all"):
            path = generate_ai_video(key, config)
            if path:
                tool_results["ai"] = path

        # Replicate AI video
        if args.method in ("replicate", "all"):
            path = generate_replicate_video(key, config)
            if path:
                tool_results["replicate"] = path

        results[key] = tool_results

    # Print summary
    print(f"\n{'='*50}")
    print("RESULTS SUMMARY")
    print(f"{'='*50}")
    for key, paths in results.items():
        print(f"\n{TOOLS[key]['name']}:")
        for method, path in paths.items():
            size = os.path.getsize(path) / 1024 if os.path.exists(path) else 0
            print(f"  [{method}] {path} ({size:.0f} KB)")
        if not paths:
            print("  (no videos generated)")

    # Update content JSON with video paths
    print(f"\n{'='*50}")
    print("NEXT STEPS")
    print(f"{'='*50}")
    print("1. Screen recordings are ready in public/tools/")
    print("2. For AI videos, set API keys:")
    print("   export FAL_KEY=your_key        # Free at https://fal.ai/dashboard/keys")
    print("   export REPLICATE_API_TOKEN=xxx  # Free at https://replicate.com")
    print("3. Update content JSON 'toolVideo' fields to point to generated videos")
    print("4. Run: npm run render:wealth")


if __name__ == "__main__":
    main()
