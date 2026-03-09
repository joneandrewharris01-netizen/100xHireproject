import type { ThemeConfig } from "../types/themes";
import { BASE_THEME } from "./base";

// Dark + cyan terminal — hacker aesthetic, authoritative
export const WEALTH_THEME: ThemeConfig = {
  ...BASE_THEME,
  name: "wealth",
  colors: {
    ...BASE_THEME.colors,
    accent: "#00D4FF",
    accentLight: "#33E0FF",
    accentDark: "#009FBF",
    termAccent: "#00D4FF",
  },
  captions: {
    ...BASE_THEME.captions,
    activeColor: "#00D4FF",
    glowColor: "rgba(0, 212, 255, 0.6)",
  },
};
