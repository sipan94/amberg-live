# Amberg Live – App (iPhone & Android)

Expo / React Native. Holt alle Daten über die App-API der Website (`/api/v1`, siehe
[../docs/API.md](../docs/API.md)). Texte der App: `src/i18n/de.ts`, Farben: `src/theme.ts`
(dieselben wie `tailwind.config.js`).

## Auf dem eigenen Handy testen (Expo Go)

Voraussetzung: Handy und Computer im **selben WLAN**.

1. **Expo Go** aus dem App Store / Play Store installieren.
2. Die Website so starten, dass das Handy sie erreicht (`--host 0.0.0.0`):

   ```bash
   .venv\Scripts\flask.exe run --debug --host 0.0.0.0 --port 5000
   ```

   Windows fragt beim ersten Mal nach der Firewall → **Private Netzwerke** erlauben.
3. In einem zweiten Terminal die App starten:

   ```bash
   cd mobile
   npm start
   ```

4. Den QR-Code scannen: iPhone mit der Kamera-App, Android direkt in Expo Go.

Die App findet den Server von selbst (gleiche Adresse wie der Computer, Port 5000).
Für einen anderen Server: `EXPO_PUBLIC_API_URL=https://… npm start`.

## Struktur

```
src/app/              Bildschirme (Expo Router: jede Datei = ein Bildschirm)
  (tabs)/             Start, Termine, Angebote, Orte, Konto
  events/[slug].tsx   Veranstaltung
  offers/[slug].tsx   Angebot
src/components/       Karten, Buttons, Texte
src/lib/api.ts        Verbindung zur API (Token, Fehler auf Deutsch)
src/lib/auth.tsx      Login-Status, Token im sicheren Speicher des Handys
src/i18n/de.ts        alle Texte der App
src/theme.ts          Farben, Schrift, Abstände
```

## Prüfen

```bash
npm run typecheck
npx expo-doctor
```

## Hinweise

- Die Schrift (Schibsted Grotesk) ist in die App eingebaut – es wird nichts aus dem Internet nachgeladen.
- Der Login-Token liegt im Schlüsselbund (iOS) bzw. Keystore (Android), nie im normalen App-Speicher.
- Unter Windows mit Smart App Control kann `npx expo export` am Hermes-Compiler scheitern;
  für Expo Go ist das egal, die Store-Builds laufen später in der Cloud (EAS).
