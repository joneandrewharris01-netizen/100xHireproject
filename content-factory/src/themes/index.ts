import type { ContentMode } from "../types/content";
import type { ThemeConfig } from "../types/themes";
import { WEALTH_THEME } from "./wealth";
import { APPS_THEME } from "./apps";
import { FINANCE_THEME } from "./finance";
import { THREED_THEME } from "./threed";
import { buildCustomTheme } from "./custom";

const THEMES: Record<Exclude<ContentMode, "custom">, ThemeConfig> = {
  wealth: WEALTH_THEME,
  apps: APPS_THEME,
  finance: FINANCE_THEME,
  threed: THREED_THEME,
};

export function getTheme(
  mode: ContentMode,
  customOverrides?: Record<string, unknown>
): ThemeConfig {
  if (mode === "custom") {
    return buildCustomTheme(customOverrides);
  }
  return THEMES[mode];
}

export { WEALTH_THEME, APPS_THEME, FINANCE_THEME, THREED_THEME, buildCustomTheme };
