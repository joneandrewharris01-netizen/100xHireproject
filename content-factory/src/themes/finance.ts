import type { ThemeConfig } from "../types/themes";
import { BASE_THEME } from "./base";

// Navy + gold — Bloomberg dashboard / premium aesthetic
export const FINANCE_THEME: ThemeConfig = {
  ...BASE_THEME,
  name: "finance",
  colors: {
    ...BASE_THEME.colors,
    bg: "#0A1628",
    bgLight: "#122040",
    bgDark: "#060E1A",
    accent: "#D4A843",
    accentLight: "#E8C468",
    accentDark: "#B8922F",
    surface: "#0F1D35",
    surfaceAlpha80: "rgba(15, 29, 53, 0.85)",
    surfaceAlpha50: "rgba(15, 29, 53, 0.5)",
    termBg: "#0A1222",
    termBorder: "#1A2A48",
    termText: "#C8D0E0",
    termAccent: "#D4A843",
  },
  captions: {
    ...BASE_THEME.captions,
    activeColor: "#D4A843",
    glowColor: "rgba(212, 168, 67, 0.6)",
  },
};
