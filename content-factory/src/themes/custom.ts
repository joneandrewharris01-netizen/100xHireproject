import type { ThemeConfig } from "../types/themes";
import { BASE_THEME } from "./base";
import { deepMerge } from "../utils/theme-utils";

// Build a custom theme by deep-merging user overrides onto base
export function buildCustomTheme(
  overrides: Record<string, unknown> = {}
): ThemeConfig {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return deepMerge(BASE_THEME as any, { ...overrides, name: "custom" }) as ThemeConfig;
}
