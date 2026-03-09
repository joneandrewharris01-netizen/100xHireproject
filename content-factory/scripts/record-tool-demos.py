"""
Record screen demo videos of tools being used.
Playwright navigates each tool's website — scrolling, clicking, hovering —
to create realistic b-roll screen recordings for reels.
"""
import sys
import os
import time
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

OUTPUT_DIR = "public/tools"

TOOLS = [
    {
        "name": "n8n",
        "output": "n8n-demo.webm",
        "steps": [
            {"action": "goto", "url": "https://n8n.io", "wait": 3},
            {"action": "dismiss_cookies"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 400, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 600, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 400, "speed": "slow"},
            {"action": "wait", "seconds": 1},
            {"action": "hover", "selector": "a:has-text('Use cases')"},
            {"action": "wait", "seconds": 2},
            {"action": "hover", "selector": "a:has-text('Product')"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": -800, "speed": "slow"},
            {"action": "wait", "seconds": 2},
        ],
    },
    {
        "name": "make",
        "output": "make-demo.webm",
        "steps": [
            {"action": "goto", "url": "https://www.make.com/en", "wait": 5},
            {"action": "dismiss_cookies"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 500, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 500, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": 400, "speed": "slow"},
            {"action": "wait", "seconds": 2},
            {"action": "hover", "selector": "a:has-text('Solutions')"},
            {"action": "wait", "seconds": 2},
            {"action": "scroll", "y": -600, "speed": "slow"},
            {"action": "wait", "seconds": 2},
        ],
    },
]


def smooth_scroll(page, y_delta, duration_ms=1500):
    """Smooth scroll by y_delta pixels over duration_ms."""
    steps = 30
    step_delay = duration_ms / steps
    step_y = y_delta / steps
    for _ in range(steps):
        page.evaluate(f"window.scrollBy(0, {step_y})")
        page.wait_for_timeout(int(step_delay))


def dismiss_cookies(page):
    """Try to dismiss cookie/consent banners."""
    page.evaluate("""
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            const txt = b.textContent.trim().toLowerCase();
            if (txt.includes('accept') || txt === 'understood' || txt === 'got it' || txt === 'ok') {
                b.click();
                break;
            }
        }
    """)
    page.wait_for_timeout(1000)
    # Also hide any remaining overlays
    page.evaluate("""
        const overlays = document.querySelectorAll('[class*=cookie], [id*=cookie], [class*=consent]');
        overlays.forEach(el => el.style.display = 'none');
    """)
    # Dismiss promo banners
    page.evaluate("""
        const close = document.querySelectorAll('[aria-label="Close"], button[class*=close], [aria-label="close"]');
        close.forEach(b => { try { b.click(); } catch(e) {} });
    """)
    page.wait_for_timeout(500)


def run_steps(page, steps):
    """Execute a sequence of recording steps."""
    for step in steps:
        action = step["action"]
        try:
            if action == "goto":
                print(f"    Navigating to {step['url']}...")
                page.goto(step["url"], wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(step.get("wait", 3) * 1000)
            elif action == "dismiss_cookies":
                print("    Dismissing cookies...")
                dismiss_cookies(page)
            elif action == "wait":
                page.wait_for_timeout(step["seconds"] * 1000)
            elif action == "scroll":
                print(f"    Scrolling {step['y']}px...")
                smooth_scroll(page, step["y"])
            elif action == "hover":
                print(f"    Hovering {step['selector']}...")
                try:
                    el = page.locator(step["selector"]).first
                    if el.is_visible(timeout=2000):
                        el.hover()
                except:
                    pass
            elif action == "click":
                print(f"    Clicking {step['selector']}...")
                try:
                    el = page.locator(step["selector"]).first
                    if el.is_visible(timeout=2000):
                        el.click()
                except:
                    pass
        except Exception as e:
            print(f"    Step error ({action}): {e}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for tool in TOOLS:
            print(f"\nRecording {tool['name']}...")
            video_path = os.path.join(OUTPUT_DIR, tool["output"])

            ctx = browser.new_context(
                viewport={"width": 1280, "height": 720},
                device_scale_factor=1,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                record_video_dir=OUTPUT_DIR,
                record_video_size={"width": 1280, "height": 720},
            )

            page = ctx.new_page()
            run_steps(page, tool["steps"])

            # Close context to flush the video
            page.close()
            ctx.close()

            # Playwright saves with a random name, find and rename it
            import glob
            webm_files = sorted(
                glob.glob(os.path.join(OUTPUT_DIR, "*.webm")),
                key=os.path.getmtime,
                reverse=True,
            )
            if webm_files:
                latest = webm_files[0]
                if os.path.abspath(latest) != os.path.abspath(video_path):
                    if os.path.exists(video_path):
                        os.remove(video_path)
                    os.rename(latest, video_path)
                print(f"  Saved: {video_path} ({os.path.getsize(video_path) / 1024:.0f} KB)")

        browser.close()
    print("\nDone! Now convert to mp4 for Remotion.")


if __name__ == "__main__":
    main()
