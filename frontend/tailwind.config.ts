import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#f0fdfa",
          100: "#ccfbf1",
          200: "#99f6e4",
          300: "#5eead4",
          400: "#2dd4bf",
          500: "#0d9488",
          600: "#0f766e",
          700: "#0b5f59",
          800: "#115e59",
          900: "#134e4a",
          950: "#0a2a27",
        },
        warm: {
          50:  "#fdfaf5",
          100: "#f7f1e8",
          200: "#ede3d0",
        },
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
      boxShadow: {
        "card": "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)",
        "card-md": "0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.05)",
        "inner-sm": "inset 0 1px 2px 0 rgb(0 0 0 / 0.05)",
      },
      animation: {
        "fade-in":      "fadeIn 0.2s ease-out",
        "slide-up":     "slideUp 0.25s ease-out",
        "float":        "float 6s ease-in-out infinite",
        "float-delay":  "float 6s ease-in-out 2s infinite",
        "float-slow":   "float 9s ease-in-out 1s infinite",
        "shimmer":      "shimmer 2.5s linear infinite",
        "glow-pulse":   "glowPulse 3s ease-in-out infinite",
        "gradient-x":   "gradientX 5s ease infinite",
        "spin-slow":    "spin 12s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%":   { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%":      { transform: "translateY(-20px)" },
        },
        shimmer: {
          "0%":   { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(200%)" },
        },
        glowPulse: {
          "0%, 100%": { boxShadow: "0 0 24px rgba(15,118,110,0.25), 0 0 60px rgba(15,118,110,0.08)" },
          "50%":      { boxShadow: "0 0 48px rgba(15,118,110,0.50), 0 0 110px rgba(15,118,110,0.18)" },
        },
        gradientX: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%":      { backgroundPosition: "100% 50%" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
