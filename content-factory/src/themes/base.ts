import type { ThemeConfig } from "../types/themes";

// Shared defaults — modes override colors and captions
export const BASE_THEME: ThemeConfig = {
  name: "base",
  colors: {
    bg: "#0B0F19",
    bgLight: "#111827",
    bgDark: "#060911",
    accent: "#00D4FF",
    accentLight: "#33E0FF",
    accentDark: "#009FBF",
    text: "#FFFFFF",
    textSoft: "#C8D0E0",
    muted: "#6B7A99",
    surface: "#141824",
    surfaceAlpha80: "rgba(20, 24, 36, 0.85)",
    surfaceAlpha50: "rgba(20, 24, 36, 0.5)",
    red: "#FF4D4D",
    yellow: "#FFB800",
    termBg: "#0A0E16",
    termBorder: "#1E2A3A",
    termText: "#C8D0E0",
    termAccent: "#00D4FF",
  },
  fonts: {
    heading: "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    body: "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    mono: "'Cascadia Code', 'Fira Code', 'Courier New', monospace",
  },
  captions: {
    fontSize: 52,
    activeFontSize: 66,
    activeColor: "#00D4FF",
    inactiveColor: "#FFFFFF",
    glowColor: "rgba(0, 212, 255, 0.6)",
    top: 1530,
  },
  spacing: {
    xs: 8,
    sm: 16,
    md: 24,
    lg: 40,
    xl: 64,
  },
  video: {
    width: 1080,
    height: 1920,
    fps: 30,
  },
};
