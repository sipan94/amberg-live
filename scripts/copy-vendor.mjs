// Copies third-party browser files from node_modules into app/static/vendor,
// so they are served from our own domain (no CDN, no visitor IPs leaked).
import { cpSync, mkdirSync } from "node:fs";

const files = [
  ["node_modules/leaflet/dist/leaflet.js", "app/static/vendor/leaflet/leaflet.js"],
  ["node_modules/leaflet/dist/leaflet.css", "app/static/vendor/leaflet/leaflet.css"],
  ["node_modules/leaflet/LICENSE", "app/static/vendor/leaflet/LICENSE"],
];

mkdirSync("app/static/vendor/leaflet", { recursive: true });
for (const [from, to] of files) {
  cpSync(from, to);
  console.log(`copied ${to}`);
}
