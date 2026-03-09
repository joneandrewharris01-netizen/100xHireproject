// Theme color palette
export interface ThemeColors {
  bg: string;
  bgLight: string;
  bgDark: string;
  accent: string;
  accentLight: string;
  accentDark: string;
  text: string;
  textSoft: string;
  muted: string;
  surface: string;
  surfaceAlpha80: string;
  surfaceAlpha50: string;
  red: string;
  yellow: string;
  termBg: string;
  termBorder: string;
  termText: string;
  termAccent: string;
}

// Theme font families
export interface ThemeFonts {
  heading: string;
  body: string;
  mono: string;
}

// Caption styling
export interface ThemeCaptionStyle {
  fontSize: number;
  activeFontSize: number;
  activeColor: string;
  inactiveColor: string;
  glowColor: string;
  top: number;
}

// Complete theme configuration
export interface ThemeConfig {
  name: string;
  colors: ThemeColors;
  fonts: ThemeFonts;
  captions: ThemeCaptionStyle;
  spacing: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
  };
  video: {
    width: number;
    height: number;
    fps: number;
  };
}
