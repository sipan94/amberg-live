# App in den App Store und Google Play bringen

Die App (`mobile/`) wird mit **EAS** (Expo) in der Cloud gebaut – ein Mac oder Android Studio
ist nicht nötig. Diese Anleitung geht Schritt für Schritt vom fertigen Code bis zur App im Store.

## 0. Vorher erledigen

| Was | Warum |
|---|---|
| Website läuft öffentlich unter **https://amberg-live.de** (siehe [DEPLOYMENT.md](DEPLOYMENT.md)) | Die App holt alle Daten von dort. Andere Adresse? In `mobile/eas.json` bei `EXPO_PUBLIC_API_URL` ändern. |
| Impressum, Datenschutz, Nutzungsbedingungen sind ausgefüllt | Beide Stores verlangen eine Datenschutz-URL. |
| **Expo-Konto** (kostenlos) auf expo.dev | Für die Cloud-Builds. |
| **Apple Developer Program** (99 $/Jahr) | Nur so kommt die App in den App Store. Für Vereine/Firmen: als Organisation anmelden (braucht eine D-U-N-S-Nummer, kostenlos, dauert ein paar Tage). |
| **Google Play Console** (25 $ einmalig) | Für Google Play. Neue private Konten müssen vor dem Start 14 Tage mit mindestens 12 Testern testen – als Organisation entfällt das. |

## 1. Projekt mit Expo verbinden (einmalig)

```bash
cd mobile
npx eas-cli@latest login
npx eas-cli@latest init
```

`init` trägt eine Projekt-ID in `app.json` ein – diese Änderung committen.

## 2. Testversion fürs Android-Handy

```bash
npx eas-cli@latest build -p android --profile preview
```

Am Ende gibt es einen Link/QR-Code zu einer `.apk`. Auf dem Android-Handy öffnen und installieren.
Diese Version spricht bereits mit der echten Website.

Für das iPhone gibt es Testversionen über **TestFlight** (Schritt 4) – das ist bei Apple der normale Weg.

## 3. Store-Versionen bauen

```bash
npx eas-cli@latest build -p ios --profile production
npx eas-cli@latest build -p android --profile production
```

- Beim ersten iOS-Build fragt EAS nach dem Apple-Konto und erstellt Zertifikate selbst – einfach „Ja“ sagen.
- Beim ersten Android-Build erstellt EAS den Signatur-Schlüssel und bewahrt ihn sicher auf. **Nicht löschen** –
  ohne ihn lassen sich keine Updates mehr veröffentlichen.
- Die Build-Nummer zählt EAS bei jedem Build selbst hoch (`autoIncrement`). Die sichtbare Version
  (`1.0.0`) steht in `app.json` → `version`.

## 4. Hochladen

**iOS** (landet in App Store Connect und TestFlight):

```bash
npx eas-cli@latest submit -p ios --profile production
```

**Android:** Die **allererste** Version einmal von Hand hochladen: Play Console → App erstellen →
„Test und Release“ → *Interner Test* → die `.aab`-Datei aus dem EAS-Build hochladen.
Danach geht es auch mit `npx eas-cli@latest submit -p android` (braucht einen Google-Service-Account,
die EAS-Anleitung führt durch).

## 5. Store-Einträge ausfüllen

### Texte (Vorschlag)

**Name:** Amberg Live
**Untertitel (iOS, max. 30 Zeichen):** Was ist los in Amberg?
**Kurzbeschreibung (Android, max. 80 Zeichen):** Veranstaltungen, Angebote und Vereine aus Amberg – alles an einem Ort.

**Beschreibung:**

> Was ist los in Amberg? Amberg Live zeigt dir Konzerte, Märkte, Feste, Führungen, Sport und Vereinsleben
> in der Stadt – heute, am Wochenende und in den nächsten Wochen.
>
> • Termine als Liste, im Monatskalender oder auf der Karte
> • Filter nach Kategorie, Zeitraum und „kostenlos“
> • Merkliste mit Erinnerung vor Beginn
> • Termine in den eigenen Kalender übernehmen, teilen, Route planen
> • Aktuelle Angebote von Amberger Geschäften
> • Geschäfte und Vereine mit Öffnungszeiten und Kontakt
>
> Für Geschäfte und Vereine: Trag deine Veranstaltungen und Angebote kostenlos selbst ein – direkt in der App.
>
> Datenschutz: keine Werbung, kein Tracking. Merkliste und Erinnerungen bleiben auf deinem Handy.

**Stichwörter (iOS):** Amberg,Veranstaltungen,Events,Oberpfalz,Termine,Vereine,Angebote,Konzerte,Märkte,Kalender
**Kategorie:** Lifestyle (zweite Kategorie: Reisen)

### Links

| Feld | URL |
|---|---|
| Datenschutz | https://amberg-live.de/datenschutz |
| Support / Kontakt | https://amberg-live.de/kontakt |
| Konto löschen (Google verlangt eine Web-Adresse) | https://amberg-live.de/konto/loeschen |

### Datenschutz-Angaben

**Apple „App-Datenschutz“** – Daten, die mit der Person verknüpft sind:
- *Kontaktinformationen → E-Mail-Adresse* (nur bei Konten für Geschäfte/Vereine), Zweck: App-Funktionalität.
- *Nutzerinhalte → Fotos, sonstige Inhalte* (Einträge von Geschäften/Vereinen), Zweck: App-Funktionalität.
- **Kein Tracking.** Keine Analyse-/Werbe-SDKs.

**Google „Datensicherheit“:**
- Erhobene Daten: E-Mail-Adresse, Fotos, sonstige nutzergenerierte Inhalte – nur bei Konten, nicht weitergegeben.
- Daten werden verschlüsselt übertragen (HTTPS): **Ja**.
- Nutzer können die Löschung beantragen: **Ja** (in der App unter Konto → Konto löschen, und auf der Website).

**Altersfreigabe:** Fragebogen ehrlich ausfüllen – keine Gewalt/Glücksspiel → in der Regel 4+ / USK 0.
Hinweis: Nutzer können Inhalte eintragen; alle Einträge werden vor der Veröffentlichung geprüft.

### Screenshots

Mindestens 3–5 Bilder, am besten: Start, Termine-Liste, Kalender, Veranstaltung, Mein Bereich.

| Store | Größe |
|---|---|
| App Store, iPhone 6,9″ | 1320 × 2868 px (Pflicht) |
| App Store, iPad 13″ | 2064 × 2752 px (nur nötig, weil `supportsTablet` an ist – sonst in `app.json` auf `false` setzen) |
| Google Play, Telefon | z. B. 1080 × 1920 px |
| Google Play, Feature-Grafik | 1024 × 500 px |

Screenshots am einfachsten auf dem eigenen Handy mit der Testversion machen.

### Für die Apple-Prüfung

Apple will den Bereich hinter dem Login sehen. Unter *App-Review-Informationen* ein **Test-Konto**
(Geschäft, bestätigt, mit Profil) angeben – nicht das Admin-Konto. Notiz z. B.:
„Login unter Konto → Anmelden. Neue Einträge erscheinen erst nach Prüfung durch die Redaktion.“

## 6. Updates

1. Code ändern, `version` in `mobile/app.json` erhöhen (z. B. `1.0.1`).
2. Schritte 3 und 4 wiederholen.

Server-Änderungen (Website/API) brauchen **kein** App-Update, solange die API gleich bleibt –
neue Felder hinzufügen ist in Ordnung, vorhandene umbenennen oder entfernen nicht (alte App-Versionen
bleiben noch lange auf Handys).

## Was die App bewusst nicht braucht

- **Push-Server / Apple-Push-Zertifikat:** Erinnerungen sind lokale Mitteilungen des Handys.
- **Standort, Kamera, Mikrofon:** abgeschaltet (`app.json` → `blockedPermissions`), es wird nur ein Foto aus der Galerie gewählt.
- **Verschlüsselungs-Exportangaben:** Die App nutzt nur Standard-HTTPS (`usesNonExemptEncryption: false`).
