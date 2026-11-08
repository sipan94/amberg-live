/** Tailwind v3 (pure JavaScript – no native binaries, works under strict Windows app policies). */
module.exports = {
  content: ["./app/templates/**/*.html", "./app/static/js/**/*.js"],
  darkMode: "class", // .dark on <html>, set by theme-init.js
  theme: {
    extend: {
      colors: {
        // Neutrals: warm, softened greys (Amberg sandstone & slate roofs) instead of Tailwind's default stone.
        // The darkest steps are deliberately not black, so dark mode feels calm rather than harsh.
        stone: {
          50: "#f6f5f2",
          100: "#eeece7",
          200: "#e1ded7",
          300: "#cbc6bd",
          400: "#a39d92",
          500: "#736d63", // ≥4.5:1 on the light canvas for small hint text
          600: "#625d55",
          700: "#4a4640",
          800: "#34302b",
          900: "#24211d",
          950: "#1a1815",
        },
        // City colours, softened: honey gold instead of signal yellow (Stadtfahne Schwarz – Gold – Schwarz).
        // 400 = buttons/accents (dark text on top), 700–800 = gold text on light backgrounds (WCAG AA+).
        gold: {
          50: "#fdf8ec",
          100: "#f9edcc",
          200: "#f2d894",
          300: "#ecc25e",
          400: "#e3a92b",
          500: "#cc8f1c",
          600: "#a87215",
          700: "#855815",
          800: "#6a4616",
          900: "#573a16",
          950: "#321f08",
        },
        // Warm slate instead of pure flag black (hero, logo mark).
        flag: "#2a2520",
      },
      fontFamily: {
        // Self-hosted variable font (app/static/vendor/fonts), system fonts as fallback.
        sans: ['"Schibsted Grotesk"', "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "Arial", "sans-serif"],
      },
      boxShadow: {
        // Soft, diffuse elevation (alpha < 0.08)
        soft: "0 1px 2px rgba(36, 33, 29, 0.04), 0 2px 8px rgba(36, 33, 29, 0.05)",
        lift: "0 2px 4px rgba(36, 33, 29, 0.05), 0 8px 24px rgba(36, 33, 29, 0.07)",
      },
    },
  },
  plugins: [],
};
