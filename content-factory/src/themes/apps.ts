import type { ThemeConfig } from "../types/themes";
import { BASE_THEME } from "./base";

// Dark + green — code editor / GitHub-dark aesthetic
export const APPS_THEME: ThemeConfig = {
  ...BASE_THEME,
  name: "apps",
  colors: {
    ...BASE_THEME.colors,
    accent: "#22C55E",
    accentLight: "#4ADE80",
    accentDark: "#16A34A",
    termBg: "#0D1117",
    termBorder: "#21262D",
    termText: "#C9D1D9",
    termAccent: "#22C55E",
  },
  captions: {
    ...BASE_THEME.captions,
    activeColor: "#22C55E",
    glowColor: "rgba(34, 197, 94, 0.6)",
  },
};
