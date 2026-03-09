/**
 * Render orchestrator: pick content → generate TTS → render video
 *
 * Usage:
 *   npx ts-node --project tsconfig.scripts.json scripts/render.ts --mode wealth
 *   npx ts-node --project tsconfig.scripts.json scripts/render.ts --mode apps
 */

import { execSync } from "child_process";
import * as path from "path";
import * as fs from "fs";

const PYTHON =
  "C:\\Users\\Admin\\AppData\\Local\\Programs\\Python\\Python311\\python.exe";
const ROOT = path.resolve(__dirname, "..");

function run(cmd: string, label: string) {
  console.log(`\n=== ${label} ===`);
  console.log(`> ${cmd}\n`);
  execSync(cmd, { stdio: "inherit", cwd: ROOT });
}

function main() {
  const args = process.argv.slice(2);
  const modeIdx = args.indexOf("--mode");
  const mode = modeIdx >= 0 ? args[modeIdx + 1] : "wealth";
  const validModes = ["wealth", "apps", "finance", "custom", "threed"];

  if (!validModes.includes(mode)) {
    console.error(`Invalid mode: ${mode}. Valid: ${validModes.join(", ")}`);
    process.exit(1);
  }

  const compositionMap: Record<string, string> = {
    wealth: "WealthVideo",
    apps: "AppsVideo",
    finance: "FinanceVideo",
    custom: "CustomVideo",
    threed: "ThreeDVideo",
  };

  const compositionId = compositionMap[mode];
  const outputDir = path.join(ROOT, "out", mode);
  const outputFile = path.join(outputDir, "video.mp4");

  // Ensure output directory exists
  fs.mkdirSync(outputDir, { recursive: true });

  // Step 1: Pick content
  // --file flag passed through from CLI, otherwise picks randomly from content/{mode}/
  const fileIdx = args.indexOf("--file");
  const fileArg = fileIdx >= 0 ? ` --file ${args[fileIdx + 1]}` : "";
  run(
    `"${PYTHON}" scripts/pick-content.py --mode ${mode}${fileArg}`,
    "PICK CONTENT"
  );

  // Step 2: Generate audio (TTS + Whisper timestamps)
  run(`"${PYTHON}" scripts/generate-audio.py`, "GENERATE AUDIO");

  // Step 3: Render with Remotion
  run(
    `npx remotion render src/index.ts ${compositionId} "${outputFile}" --codec h264 --crf 18`,
    "RENDER VIDEO"
  );

  console.log(`\n✅ Done! Output: ${outputFile}`);
}

main();
