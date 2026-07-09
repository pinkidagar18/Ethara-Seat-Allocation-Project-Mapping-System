import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Dark futuristic / glassmorphism — exact palette as specified:
        // primary #667eea, secondary #764ba2, accent #f093fb, dark #0a0a0a, light #ffffff
        bg: "#0A0A0A",
        surface: "#131318",
        ink: "#FFFFFF",
        "ink-muted": "#9B9BB0",
        border: "#22222E",
        brand: {
          DEFAULT: "#667eea", // --primary
          dark: "#764ba2",    // --secondary (doubles as hover/CTA variant per spec)
          light: "#1A1A33",   // solid dark indigo tint for active states / badges
        },
        accent: "#f093fb",    // --accent — headline highlights, gradient end, glow
        available: "#34D399",
        occupied: "#FBBF24",
        danger: "#F87171",
        hold: "#9B9BB0",
      },
      fontFamily: {
        display: ["var(--font-space-grotesk)", "sans-serif"],
        body: ["var(--font-inter)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      boxShadow: {
        card: "0 8px 32px rgba(0, 0, 0, 0.6)",
        glow: "0 0 24px rgba(102, 126, 234, 0.35)",
      },
      borderRadius: {
        card: "10px",
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};
export default config;
