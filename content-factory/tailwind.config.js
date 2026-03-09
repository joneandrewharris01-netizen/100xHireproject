/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0B0F19",
          light: "#131825",
          lighter: "#1A2035",
          border: "#2A3050",
        },
        wealth: "#00D4FF",
        apps: "#22C55E",
        finance: "#D4A843",
        custom: "#8B5CF6",
      },
      fontFamily: {
        sans: ["Segoe UI", "system-ui", "sans-serif"],
        mono: ["Cascadia Code", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
