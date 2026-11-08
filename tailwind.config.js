/** Tailwind v3 (pure JavaScript – no native binaries, works under strict Windows app policies). */
module.exports = {
  content: ["./app/templates/**/*.html", "./app/static/js/**/*.js"],
  darkMode: "class", // .dark on <html>, set by theme-init.js
  theme: {
    extend: {
      colors: {
        // Amberg city colors (Stadtfahne: Schwarz – Gold – Schwarz, Satzung von 1966).
        // Heraldic gold as the accent; 400 is the "flag gold". Dark shades are for text on light backgrounds.
        gold: {
          50: "#fffbea",
          100: "#fff3c4",
          200: "#ffe685",
          300: "#ffd84a",
          400: "#f5c400",
          500: "#dcaa00",
          600: "#b38600",
          700: "#866300",
          800: "#664c05",
          900: "#523d09",
          950: "#2e2102",
        },
        // Flag black (slightly warm so it sits well with the stone greys).
        flag: "#0d0c0b",
      },
      fontFamily: {
        // System fonts only: nothing is loaded from external servers.
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "Helvetica Neue", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};
