// Copies third-party browser files from node_modules into app/static/vendor,
// so they are served from our own domain (no CDN, no visitor IPs leaked).
import { cpSync, mkdirSync } from "node:fs";

const font = "node_modules/@fontsource-variable/schibsted-grotesk";
const files = [
  ["node_modules/leaflet/dist/leaflet.js", "app/static/vendor/leaflet/leaflet.js"],
  ["node_modules/leaflet/dist/leaflet.css", "app/static/vendor/leaflet/leaflet.css"],
  ["node_modules/leaflet/LICENSE", "app/static/vendor/leaflet/LICENSE"],
  // Schibsted Grotesk (variable weight, SIL Open Font License): Latin + Latin Extended
  [`${font}/files/schibsted-grotesk-latin-wght-normal.woff2`, "app/static/vendor/fonts/schibsted-grotesk-latin.woff2"],
  [`${font}/files/schibsted-grotesk-latin-ext-wght-normal.woff2`, "app/static/vendor/fonts/schibsted-grotesk-latin-ext.woff2"],
  [`${font}/LICENSE`, "app/static/vendor/fonts/LICENSE-OFL.txt"],
];

for (const dir of ["app/static/vendor/leaflet", "app/static/vendor/fonts"]) {
  mkdirSync(dir, { recursive: true });
}
for (const [from, to] of files) {
  cpSync(from, to);
  console.log(`copied ${to}`);
}
