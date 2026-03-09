"""
Pick a random content script for the given mode and write it to src/data/today.json.

Usage:
  python pick-content.py --mode wealth
  python pick-content.py --mode apps
  python pick-content.py --mode finance
  python pick-content.py --mode custom --file content/custom/my-script.json
"""

import sys
import os
import json
import glob
import random
import argparse
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY_JSON = os.path.join(PROJECT_ROOT, "src", "data", "today.json")


def pick_script(mode: str, specific_file: str = None) -> dict:
    """Pick a content script JSON from content/{mode}/."""
    if specific_file:
        path = os.path.join(PROJECT_ROOT, specific_file)
        if not os.path.exists(path):
            print(f"[Pick] ERROR: File not found: {path}")
            sys.exit(1)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    content_dir = os.path.join(PROJECT_ROOT, "content", mode)
    scripts = glob.glob(os.path.join(content_dir, "*.json"))

    if not scripts:
        print(f"[Pick] ERROR: No scripts found in {content_dir}")
        sys.exit(1)

    chosen = random.choice(scripts)
    print(f"[Pick] Chose: {os.path.basename(chosen)}")

    with open(chosen, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Pick content for rendering")
    parser.add_argument("--mode", required=True, choices=["wealth", "apps", "finance", "custom", "threed"])
    parser.add_argument("--file", default=None, help="Specific script file (for custom mode)")
    args = parser.parse_args()

    script = pick_script(args.mode, args.file)

    # Ensure mode is set
    script["mode"] = args.mode

    # Build today.json structure
    today = {
        "script": script,
        "audio": {
            "audioFile": "",
            "durationSeconds": 25,
            "words": [],
        },
        "generatedAt": datetime.now().isoformat(),
    }

    with open(TODAY_JSON, "w", encoding="utf-8") as f:
        json.dump(today, f, indent=2, ensure_ascii=False)

    print(f"[Pick] Written to {TODAY_JSON}")
    print(f"[Pick] Mode: {args.mode}, Title: {script.get('title', 'untitled')}")


if __name__ == "__main__":
    main()
