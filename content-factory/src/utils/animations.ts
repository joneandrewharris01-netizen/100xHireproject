import { spring, interpolate } from "remotion";

// ===== Spring Presets =====
export const FAST = { damping: 12, mass: 0.3, stiffness: 350 };
export const SNAP = { damping: 14, mass: 0.25, stiffness: 400 };
export const BOUNCY = { damping: 12, mass: 0.5, stiffness: 200 };
export const SMOOTH = { damping: 20, mass: 0.8, stiffness: 120 };
export const SNAPPY = { damping: 18, mass: 0.2, stiffness: 500 };

// ===== Animation Modes =====
export type AnimMode =
  | "slamLeft"
  | "slamRight"
  | "slamTop"
  | "slamBottom"
  | "zoomCenter"
  | "scaleUp";

export const ANIM_CYCLE: AnimMode[] = [
  "slamLeft",
  "zoomCenter",
  "slamRight",
  "slamTop",
  "scaleUp",
  "slamBottom",
  "zoomCenter",
];

// ===== Visibility System =====
const EXIT_DUR = 4; // faster exits

export function vis(
  frame: number,
  fps: number,
  enterAt: number,
  exitAt: number,
  exitDur: number = EXIT_DUR
) {
  const show = frame >= enterAt && frame < exitAt + exitDur;
  const enter = spring({ frame: frame - enterAt, fps, config: FAST });
  const exit = interpolate(frame, [exitAt, exitAt + exitDur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = enter * (1 - exit);
  return { show, enter, exit, opacity };
}

// ===== Continuous Motion Helpers — nothing stays still =====

/** Gentle floating up/down. Returns Y offset in px. */
export function float(frame: number, speed = 0.04, amplitude = 8): number {
  return Math.sin(frame * speed) * amplitude;
}

/** Scale breathing. Returns scale value around 1.0. */
export function breathe(frame: number, speed = 0.06, amount = 0.02): number {
  return 1 + Math.sin(frame * speed) * amount;
}

/** Glow pulse intensity 0-1. */
export function glowPulse(frame: number, speed = 0.08): number {
  return 0.6 + Math.sin(frame * speed) * 0.4;
}

/** Subtle horizontal sway. Returns X offset in px. */
export function sway(frame: number, speed = 0.03, amplitude = 5): number {
  return Math.sin(frame * speed + 0.5) * amplitude;
}

/** Subtle rotation. Returns degrees. */
export function tilt(frame: number, speed = 0.025, amplitude = 1.5): number {
  return Math.sin(frame * speed) * amplitude;
}

/** Stagger delay: returns frame offset for item at index */
export function stagger(index: number, gap = 6): number {
  return index * gap;
}

// ===== Transform Builders =====
export function getEnterTransform(mode: AnimMode, enter: number): string {
  const progress = 1 - enter;
  switch (mode) {
    case "slamLeft":
      return `translateX(${-300 * progress}px)`;
    case "slamRight":
      return `translateX(${300 * progress}px)`;
    case "slamTop":
      return `translateY(${-200 * progress}px)`;
    case "slamBottom":
      return `translateY(${200 * progress}px)`;
    case "zoomCenter":
      return `scale(${0.3 + 0.7 * enter})`;
    case "scaleUp":
      return `scale(${0.5 + 0.5 * enter})`;
  }
}

export function getExitTransform(mode: AnimMode, exit: number): string {
  switch (mode) {
    case "slamLeft":
      return `translateX(${300 * exit}px)`;
    case "slamRight":
      return `translateX(${-300 * exit}px)`;
    case "slamTop":
      return `translateY(${-200 * exit}px)`;
    case "slamBottom":
      return `translateY(${200 * exit}px)`;
    case "zoomCenter":
      return `scale(${1 - 0.7 * exit})`;
    case "scaleUp":
      return `scale(${1 + 0.5 * exit})`;
  }
}

// ===== Slide Directions for Captions =====
export type SlideDir = "left" | "right" | "zoom" | "top" | "bottom";

export const SLIDE_CYCLE: SlideDir[] = [
  "left",
  "right",
  "zoom",
  "top",
  "bottom",
  "right",
  "left",
  "zoom",
  "bottom",
  "top",
];

export function getSlideTransform(dir: SlideDir, progress: number): string {
  const offset = 1 - progress;
  switch (dir) {
    case "left":
      return `translateX(${-120 * offset}px)`;
    case "right":
      return `translateX(${120 * offset}px)`;
    case "zoom":
      return `scale(${0.4 + 0.6 * progress})`;
    case "top":
      return `translateY(${-80 * offset}px)`;
    case "bottom":
      return `translateY(${80 * offset}px)`;
  }
}
