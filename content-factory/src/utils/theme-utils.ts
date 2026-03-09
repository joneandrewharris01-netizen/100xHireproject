// Deep merge utility for custom theme overrides
export function deepMerge<T extends Record<string, unknown>>(
  base: T,
  overrides: Record<string, unknown>
): T {
  const result = { ...base } as Record<string, unknown>;

  for (const key of Object.keys(overrides)) {
    const baseVal = result[key];
    const overVal = overrides[key];

    if (
      baseVal &&
      overVal &&
      typeof baseVal === "object" &&
      typeof overVal === "object" &&
      !Array.isArray(baseVal) &&
      !Array.isArray(overVal)
    ) {
      result[key] = deepMerge(
        baseVal as Record<string, unknown>,
        overVal as Record<string, unknown>
      );
    } else {
      result[key] = overVal;
    }
  }

  return result as T;
}
