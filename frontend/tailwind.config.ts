import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        tempo: {
          bg: "#0a0f14",
          surface: "#121a22",
          border: "#1e2a36",
          accent: "#3dd6c6",
          warn: "#f5a623",
          danger: "#e85d5d",
          muted: "#8b9aab",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
