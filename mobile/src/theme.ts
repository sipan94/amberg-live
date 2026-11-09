/** Colours and type – the same palette as the website (tailwind.config.js). */
import { useColorScheme } from "react-native";

export const stone = {
  50: "#f6f5f2", 100: "#eeece7", 200: "#e1ded7", 300: "#cbc6bd", 400: "#a39d92", 500: "#736d63",
  600: "#625d55", 700: "#4a4640", 800: "#34302b", 900: "#24211d", 950: "#1a1815",
};
export const gold = {
  50: "#fdf8ec", 100: "#f9edcc", 200: "#f2d894", 300: "#ecc25e", 400: "#e3a92b", 500: "#cc8f1c",
  600: "#a87215", 700: "#855815", 800: "#6a4616", 900: "#573a16", 950: "#321f08",
};
export const flag = "#2a2520";

const light = {
  dark: false,
  bg: stone[50],
  card: "#ffffff",
  cardBorder: "rgba(36,33,29,0.09)",
  text: stone[900],
  textMuted: stone[500],
  textSoft: stone[700],
  accent: gold[400], // buttons (dark text on top)
  accentText: gold[800], // gold text on light backgrounds
  highlightBg: "rgba(253,248,236,0.6)",
  highlightBorder: gold[300],
  chipBg: "#ffffff",
  chipActiveBg: gold[100],
  chipActiveBorder: gold[400],
  tabBar: "rgba(255,255,255,0.96)",
  danger: "#b42318",
  success: "#2f6b3a",
};

const dark: typeof light = {
  dark: true,
  bg: stone[950],
  card: stone[900],
  cardBorder: "rgba(255,255,255,0.09)",
  text: stone[100],
  textMuted: stone[400],
  textSoft: stone[300],
  accent: gold[400],
  accentText: gold[300],
  highlightBg: "rgba(227,169,43,0.09)",
  highlightBorder: "rgba(227,169,43,0.5)",
  chipBg: stone[900],
  chipActiveBg: "rgba(227,169,43,0.15)",
  chipActiveBorder: "rgba(227,169,43,0.6)",
  tabBar: "rgba(26,24,21,0.96)",
  danger: "#f97066",
  success: "#7bc58a",
};

export type Theme = typeof light;

export function useTheme(): Theme {
  return useColorScheme() === "dark" ? dark : light;
}

/** Schibsted Grotesk, bundled with the app (no font is loaded from the internet). */
export const font = {
  regular: "SchibstedGrotesk_400Regular",
  medium: "SchibstedGrotesk_500Medium",
  semibold: "SchibstedGrotesk_600SemiBold",
  bold: "SchibstedGrotesk_700Bold",
};

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32 };
export const radius = { sm: 8, md: 12, lg: 16, pill: 999 };

/** Mixes a category colour into the card colour – like `.cover` on the website (color-mix 9 %). */
export function tint(hex: string, amount: number, base: string): string {
  const parse = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const [r1, g1, b1] = parse(hex.length === 7 ? hex : "#736d63");
  const [r2, g2, b2] = parse(base.startsWith("#") ? base : "#ffffff");
  const mix = (a: number, b: number) => Math.round(a * amount + b * (1 - amount));
  return `rgb(${mix(r1, r2)}, ${mix(g1, g2)}, ${mix(b1, b2)})`;
}
