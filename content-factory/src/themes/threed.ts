import type { ThemeConfig } from "../types/themes";
import { BASE_THEME } from "./base";

// Electric violet — 3D futuristic aesthetic
export const THREED_THEME: ThemeConfig = {
  ...BASE_THEME,
  name: "threed",
  colors: {
    ...BASE_THEME.colors,
    bg: "#08070F",
    bgLight: "#0F0D1A",
    bgDark: "#040308",
    accent: "#A855F7",
    accentLight: "#C084FC",
    accentDark: "#7C3AED",
    surface: "#110F1D",
    surfaceAlpha80: "rgba(17, 15, 29, 0.85)",
    surfaceAlpha50: "rgba(17, 15, 29, 0.5)",
    termBg: "#0A0812",
    termBorder: "#1E1535",
    termText: "#D0C8E8",
    termAccent: "#A855F7",
  },
  captions: {
    ...BASE_THEME.captions,
    activeColor: "#A855F7",
    glowColor: "rgba(168, 85, 247, 0.6)",
  },
};
