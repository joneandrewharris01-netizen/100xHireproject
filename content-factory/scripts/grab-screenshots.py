import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

TOOLS = [
    {
        "name": "n8n",
        "url": "https://n8n.io",
        "output": "public/tools/n8n-screenshot.png",
    },
    {
        "name": "make",
        "url": "https://www.make.com",
        "output": "public/tools/make-screenshot.png",
    },
]

def main():
    os.makedirs("public/tools", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            device_scale_factor=2,
        )

        for tool in TOOLS:
            print(f"Capturing {tool['name']} from {tool['url']}...")
            page = context.new_page()
            try:
                page.goto(tool["url"], wait_until="networkidle", timeout=30000)
                # Wait a bit for animations to settle
                page.wait_for_timeout(3000)
                # Dismiss cookie banners if present
                for selector in [
                    "button:has-text('Accept')",
                    "button:has-text('Got it')",
                    "button:has-text('OK')",
                    "[id*='cookie'] button",
                    "[class*='cookie'] button",
                    "[class*='consent'] button",
                ]:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible(timeout=1000):
                            btn.click()
                            page.wait_for_timeout(500)
                            break
                    except:
                        pass

                page.wait_for_timeout(1000)
                page.screenshot(path=tool["output"], type="png")
                print(f"  Saved to {tool['output']}")
            except Exception as e:
                print(f"  Error: {e}")
            finally:
                page.close()

        browser.close()

    print("Done!")

if __name__ == "__main__":
    main()
