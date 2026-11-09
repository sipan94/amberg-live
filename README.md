# Amberg Live

Lokaler Guide für Amberg (Oberpfalz): **Veranstaltungen, Angebote, Geschäfte & Vereine** – heute,
am Wochenende und demnächst. Geschäfte und Vereine tragen ihre Termine selbst ein, der Admin
prüft alles vor der Veröffentlichung.

- Mobile-first, installierbar als App (PWA), Dunkelmodus, in den Stadtfarben Schwarz–Gold
- Datenschutzfreundlich: kein Cookie für Besucher, keine Google-Dienste, keine CDNs, Karte erst nach Klick
- Flask · SQLAlchemy · SQLite (Entwicklung) / PostgreSQL (Produktion) · Tailwind · Leaflet/OpenStreetMap

> Deployment auf einem eigenen Server: **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**
> Schnittstelle für die iPhone-/Android-App: **[docs/API.md](docs/API.md)** · App selbst: **[mobile/README.md](mobile/README.md)**

---

## Funktionen

| Bereich | Was es kann |
|---|---|
| **Besucher** | Startseite „Heute / Wochenende / Demnächst“, Liste mit Filtern (Zeitraum, Kategorie, kostenlos, Suche), Kalender, Karte, Detailseiten mit `.ics`-Download und Teilen, Angebote, Verzeichnis, Merkliste (nur auf dem Gerät) |
| **Geschäfte & Vereine** | Registrierung mit E-Mail-Bestätigung, Profil (Logo, Titelbild, Öffnungszeiten, Kartenposition automatisch), Veranstaltungen (einmalig, wöchentlich, monatlich) und Angebote, Status + Ablehnungsgrund, Passwort ändern, Konto löschen |
| **Admin** | Prüf-Warteschlange mit Freigeben/Ablehnen (+ E-Mail an Anbieter), alles bearbeiten, „Tipp“ und Premium (mit Ablaufdatum), Nutzer sperren/löschen, Kategorien, Protokoll, anonyme Statistik |
| **SEO** | Saubere URLs mit Slugs, Meta- und Open-Graph-Tags, `sitemap.xml`, `robots.txt`, schema.org JSON-LD (Event, LocalBusiness, WebSite) |
| **Sicherheit** | CSRF überall, Argon2-Passwörter, Rate-Limits, strenge CSP und Security-Header, Bild-Prüfung + Metadaten-Entfernung, bleach für Texte, Schutz vor Open Redirect und Account-Enumeration |

## Schnellstart (lokal)

Voraussetzung: **Python 3.12+** (getestet mit 3.12 und 3.14). Node ist nur nötig, wenn du das Design änderst.

**Windows (PowerShell)**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
flask db upgrade
flask seed
flask run --debug
```

**Linux / macOS**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
flask db upgrade
flask seed
flask run --debug
```

Dann <http://localhost:5000> öffnen. `flask seed` legt Demo-Daten an und zeigt die Logins
(Admin: `ADMIN_EMAIL`, Demo-Geschäft: `cafe-vilsufer@example.com`, Passwort: `SEED_PASSWORD` aus `.env`).
E-Mails werden lokal **nicht verschickt**, sondern im Terminal ausgegeben (Bestätigungslinks kannst du dort kopieren).

## Befehle

| Befehl | Zweck |
|---|---|
| `flask run --debug` | Entwicklungsserver mit automatischem Neuladen |
| `flask seed [--reset]` | Demo-Daten (nur Entwicklung; `--reset` löscht vorher alles) |
| `flask seed-categories` | Standard-Kategorien anlegen/aktualisieren (auch in Produktion) |
| `flask create-admin EMAIL` | Admin anlegen oder bestehendes Konto zum Admin machen |
| `flask premium-expire` | Abgelaufene Premium-Einträge beenden (täglich per Timer) |
| `flask db migrate -m "…"` | Migration nach Modelländerung erzeugen |
| `flask db upgrade` | Migrationen anwenden |
| `pytest` | Tests ausführen |

## Tests

```bash
pytest            # 65 Tests: Modelle, Berechtigungen, öffentliche Seiten, Konten, Dashboard, Admin
pytest -k admin   # nur Admin-Tests
```

Die Tests nutzen eine In-Memory-Datenbank und einen temporären Upload-Ordner – deine Daten bleiben unberührt.
Hinweis für eigene Tests: Requests **nicht** innerhalb eines offenen `app.app_context()` absetzen
(siehe Kommentar in `tests/conftest.py`).

## Design / CSS ändern

Das fertige `app/static/css/app.css` ist eingecheckt – der Server braucht kein Node.

```bash
npm install
npm run build        # Leaflet nach app/static/vendor kopieren + CSS bauen
npm run watch:css    # CSS beim Bearbeiten automatisch neu bauen
python scripts/make_icons.py   # App-Icons und Teilen-Bild neu erzeugen
```

- **Farben:** `tailwind.config.js` → `gold` (Akzent, Flaggen-Gold) und `flag` (Schwarz). Stadtfarben laut
  Satzung der Stadt Amberg: Schwarz – Gold – Schwarz. Das **Stadtwappen** wird bewusst nicht verwendet
  (Nutzung durch Dritte braucht eine Genehmigung der Stadt, § 4 der Satzung).
- Tailwind ist absichtlich **v3**: v4 bringt eine native Datei mit, die strenge Windows-Richtlinien (Smart App Control) blockieren.

## Texte & Übersetzungen

Alle Oberflächentexte stehen in **`app/i18n/de.json`** (Aufruf im Template: `{{ t("events.title") }}`).
Für Englisch: `en.json` mit denselben Schlüsseln anlegen und `current_locale()` in `app/i18n/__init__.py`
pro Anfrage wählen lassen. Rechtstexte sind längere Inhalte und liegen als Templates unter `app/templates/legal/`.

**Vor dem Start ausfüllen:** alle gelb markierten `TODO`-Stellen in Impressum, Datenschutz, AGB und Kontakt –
und die Texte rechtlich prüfen lassen.

## Konfiguration (`.env`)

| Variable | Bedeutung |
|---|---|
| `APP_ENV` | `development` · `production` · `testing` |
| `SECRET_KEY` | Pflicht in Produktion, mind. 32 Zeichen: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `SITE_URL` | Öffentliche Adresse ohne `/` am Ende (für Sitemap, Open Graph, E-Mail-Links) |
| `DATABASE_URL` | leer = SQLite in `instance/`; PostgreSQL: `postgresql://user:pass@localhost/amberg_live` |
| `UPLOAD_FOLDER`, `MAX_UPLOAD_MB` | Speicherort und Größenlimit für Bilder |
| `MAIL_HOST`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_USE_TLS`, `MAIL_FROM` | SMTP-Versand; leer = Ausgabe im Log |
| `ADMIN_EMAIL` | bekommt Hinweise auf neue Einreichungen |
| `ALLOWED_HOSTS` | Produktion: erlaubte Hostnamen, kommagetrennt |
| `PROXY_COUNT` | Anzahl Reverse-Proxys davor (nginx = 1) |
| `RATELIMIT_STORAGE_URI`, `RATELIMIT_DEFAULT` | Speicher und globales Limit für Rate-Limits |
| `GEOCODER_ENABLED`, `NOMINATIM_URL` | Adresse → Kartenposition (serverseitig) |
| `LOG_LEVEL`, `LOG_DIR` | Logging |

## Projektstruktur

```
app/
  __init__.py        App-Factory (Blueprints, Extensions, Logging)
  config.py          Einstellungen je Umgebung
  security.py        Security-Header, CSP, Cache-Regeln
  templating.py      Jinja-Filter (Datum, Preis), versionierte Assets
  models/            User, Organization, Event, Offer, Category, ModerationLog, DailyStat
  public/            öffentliche Seiten, SEO, PWA
  auth/              Registrierung, Login, Passwort
  dashboard/         Bereich für Geschäfte & Vereine
  admin/             Verwaltung & Moderation
  billing/           Premium – hier wird später Stripe angebunden
  services/          Logik: Termine, Bilder, Mail, Moderation, Statistik, iCal, JSON-LD
  forms/             WTForms mit deutschen Fehlermeldungen
  api/               JSON-API für die App (/api/v1)
  i18n/de.json       alle UI-Texte
  templates/         Jinja-Templates
  static/            CSS (gebaut), JS, Icons, Leaflet
deploy/              gunicorn, systemd, nginx, Backup
docs/DEPLOYMENT.md   Server-Anleitung
docs/API.md          App-API
migrations/          Datenbank-Migrationen
tests/               pytest
```

## Wichtige Konventionen

- **Zeiten:** Veranstaltungs- und Angebotszeiten sind **Amberger Ortszeit** ohne Zeitzone gespeichert
  („jeden Freitag 19 Uhr“ bleibt 19 Uhr nach der Zeitumstellung). Technische Zeitstempel sind UTC.
- **Wiederkehrende Termine** speichern nur den ersten Termin; `app/utils/recurrence.py` berechnet die weiteren.
  Monatlich am 31. → in kürzeren Monaten am letzten Tag.
- **Moderation:** Neue und abgelehnte Einträge gehen in die Prüfung. Bei freigegebenen Einträgen lösen nur
  Änderungen an Titel, Text, Bild (bzw. Name, Logo, Titelbild, Webseite, E-Mail) eine neue Prüfung aus –
  Uhrzeit, Preis, Ort und Kategorie sind sofort online (`app/services/moderation.py`).
- **Bilder** werden geprüft, gedreht, verkleinert, als WebP gespeichert (groß + `_sm`-Variante) und von allen Metadaten befreit.

## Bezahlte Einträge (später)

`is_featured` („Tipp“) und `is_premium` („Partner“) funktionieren bereits (Badge + Platzierung oben).
Stripe-Abos kommen in **ein** Modul: `app/billing/__init__.py` (Anleitung im Docstring) –
Webhooks rufen dort `set_premium()` / `clear_premium()` auf, der Rest der App bleibt unverändert.

## Datenschutz auf einen Blick

- Einziges Cookie `al_session` nur bei Anmeldung/Formularen (technisch notwendig) → **kein Cookie-Banner**
- Merkliste, Hell/Dunkel und Karten-Zustimmung im `localStorage` des Geräts (vom Nutzer ausgelöst, § 25 Abs. 2 TDDDG)
- Statistik: anonyme Tageszähler ohne IP/Cookie; Bots werden nicht gezählt
- OpenStreetMap-Kacheln erst nach Klick auf „Karte laden“; Geokodierung läuft über den Server
- Alles selbst gehostet (Schrift = Systemschrift, Leaflet lokal)
