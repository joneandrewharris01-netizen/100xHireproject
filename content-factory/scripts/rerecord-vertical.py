"""Re-record tool websites with vertical viewport for 9:16 reels."""
import sys
import os
import glob
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "tools")
FFMPEG = r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe"

TOOLS = {
    "make": {
        "url": "https://www.make.com/en",
        "steps": [
            {"action": "goto", "url": "https://www.make.com/en", "wait": 5},
            {"action": "dismiss_cookies"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 400, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 400, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 300, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": -600, "speed": "slow"},
            {"action": "wait", "seconds": 2},
        ],
    },
    "claude": {
        "url": "https://claude.ai",
        "steps": [
            {"action": "goto", "url": "https://claude.ai", "wait": 5},
            {"action": "dismiss_cookies"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 300, "speed": "slow"},
            {"action": "wait", "seconds": 3},
            {"action": "scroll", "y": 300, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": -400, "speed": "slow"},
            {"action": "wait", "seconds": 2},
        ],
    },
}


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


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for key, config in TOOLS.items():
            print(f"\nRecording {key} (vertical 540x960 @2x)...")

            ctx = browser.new_context(
                viewport={"width": 1080, "height": 1920},
                device_scale_factor=1,
                is_mobile=True,
                has_touch=True,
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                record_video_dir=OUTPUT_DIR,
                record_video_size={"width": 1080, "height": 1920},
            )

            page = ctx.new_page()

            for step in config["steps"]:
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
                except Exception as e:
                    print(f"  Step error ({action}): {e}")

            page.close()
            ctx.close()

            # Find and rename latest webm
            webm_files = sorted(
                glob.glob(os.path.join(OUTPUT_DIR, "*.webm")),
                key=os.path.getmtime,
                reverse=True,
            )
            if webm_files:
                latest = webm_files[0]
                output_webm = os.path.join(OUTPUT_DIR, f"{key}-vertical.webm")
                output_mp4 = os.path.join(OUTPUT_DIR, f"{key}-demo-trimmed.mp4")

                if os.path.abspath(latest) != os.path.abspath(output_webm):
                    if os.path.exists(output_webm):
                        os.remove(output_webm)
                    os.rename(latest, output_webm)

                # Convert to mp4, trim first 3s of loading
                subprocess.run(
                    [
                        FFMPEG, "-y", "-ss", "3", "-i", output_webm,
                        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                        "-pix_fmt", "yuv420p", output_mp4,
                    ],
                    capture_output=True,
                )
                size_kb = os.path.getsize(output_mp4) / 1024
                print(f"  Saved: {output_mp4} ({size_kb:.0f} KB)")

        browser.close()

    print("\nDone! All recordings are vertical 1080x1920.")


if __name__ == "__main__":
    main()
