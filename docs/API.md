# App-API (`/api/v1`)

JSON-Schnittstelle für die iPhone- und Android-App. Sie nutzt **dieselben Formulare,
Prüfregeln, Bildverarbeitung und Freigabe-Regeln** wie die Website – die App ist nur ein
anderer Weg, sie auszufüllen. Alle Texte (Fehler, Datumsangaben, Preise) kommen fertig
auf Deutsch vom Server.

Code: `app/api/` · Tests: `tests/test_api.py`

## Grundregeln

| Thema | Regel |
|---|---|
| Anmeldung | `POST /auth/login` liefert einen Token. Danach jede Anfrage mit `Authorization: Bearer <token>`. |
| Token | 90 Tage gültig. In der Datenbank liegt nur der SHA-256-Hash (`api_tokens`). |
| Abmelden überall | Passwort ändern (App oder Website), Passwort zurücksetzen oder Sperre durch Admin löscht die Tokens. |
| Cookies | Die API liest **kein** Session-Cookie → kein CSRF nötig, kein Missbrauch über fremde Seiten. |
| Daten senden | JSON (`Content-Type: application/json`) oder `multipart/form-data`, wenn ein Bild dabei ist. |
| Feldnamen | Wie in den Website-Formularen (`start_date`, `start_time`, `rights_confirmed`, …). Datum `YYYY-MM-DD`, Zeit `HH:MM`. |
| Seiten | Listen nehmen `?seite=N` und liefern `page, pages, total, has_next, has_prev`. |
| Limits | Wie auf der Website (z. B. Login 10/Minute, Einreichungen 30/Stunde). |

### Antworten bei Fehlern

```json
{ "error": "Bitte prüfe deine Eingaben." }                                      // 400/401/403/404/409/413/429/500
{ "error": "Bitte prüfe deine Eingaben.", "fields": { "title": ["Pflichtfeld."] } }  // 422
```

| Status | Bedeutung |
|---|---|
| 401 | Kein oder ungültiger/abgelaufener Token → zum Login. |
| 403 `code: not_verified` | E-Mail noch nicht bestätigt. |
| 403 `code: blocked` | Konto gesperrt (beim Login). |
| 404 | Nicht gefunden – auch bei fremden Inhalten und bei Admin-Routen für Nicht-Admins. |
| 409 `code: no_profile` | Erst ein Profil (Laden/Verein) anlegen. |
| 422 | Formularfehler, pro Feld in `fields`. |

## Öffentlich (ohne Login)

| Methode & Pfad | Inhalt |
|---|---|
| `GET /meta` | Kategorien, Filter-Auswahl (Zeitraum, Preis), Links zu Impressum/Datenschutz/AGB/Kontakt, Website-URL. Einmal beim Start laden. |
| `GET /home` | Heute, Wochenende, Demnächst, aktuelle Angebote. |
| `GET /events` | Liste nach Tagen gruppiert + Tipps. Filter: `zeitraum` (alle/heute/wochenende/woche/monat), `kategorie`, `preis`, `q`, `von`, `bis`, `seite`. |
| `GET /events/calendar?monat=YYYY-MM` | Monatsansicht: Termine pro Tag, Vor-/Folgemonat. Dieselben Filter. |
| `GET /events/map` | Marker mit Koordinaten, Anzahl ohne Ort, Kachel-URL (OpenStreetMap) und Kartenmitte. |
| `GET /events/<slug>` | Details, nächste Termine, `ics_url` (Kalender), `share_text`, weitere vom Veranstalter. |
| `GET /offers`, `GET /offers/<slug>` | Aktuelle Angebote. |
| `GET /organizations?typ=&q=` | Läden & Vereine (`typ`: wie auf der Website). |
| `GET /organizations/<slug>` | Profil, Öffnungszeiten, Termine, Angebote. |
| `POST /favorites` `{"slugs": [...]}` | Kartendaten für die Merkliste. Die Merkliste selbst bleibt auf dem Handy. |

Nur freigegebene Inhalte; vergangene Termine fehlen in Listen; Serientermine werden aufgefächert.

## Konto

| Methode & Pfad | Inhalt |
|---|---|
| `POST /auth/register` | `email, password, password2, accept_terms` → immer 201 (verrät nicht, ob die Adresse existiert). |
| `POST /auth/login` | `email, password, device?` → `{token, user}`. |
| `POST /auth/logout` | Löscht nur den Token dieses Geräts. |
| `GET /auth/me` | Benutzer + eigenes Profil; Admins zusätzlich `pending` (offene Prüfungen). |
| `POST /auth/resend-verification` | Bestätigungs-Mail erneut senden. |
| `POST /auth/forgot-password` | `email` → Mail mit Link; das neue Passwort wird auf der Website gesetzt. |
| `POST /auth/change-password` | `current_password, password, password2` → andere Geräte werden abgemeldet. |
| `POST /auth/delete-account` | `password, confirm` → löscht Konto, Inhalte und Bilder (DSGVO). |

## Laden/Verein (Login nötig)

| Methode & Pfad | Inhalt |
|---|---|
| `GET /me/overview` | Benutzer, eigenes Profil, eigene Veranstaltungen & Angebote mit Status und Ablehnungsgrund. |
| `GET /me/form-options` | Kategorien, Wiederholungen, Profil-Arten, Wochentage, Rechte-Hinweis. |
| `POST`/`PUT /me/organization` | Profil anlegen/ändern (Logo `logo`, Titelbild `cover`, `remove_logo`, `remove_cover`). |
| `POST /me/events` | Veranstaltung anlegen (Bild `image`). |
| `GET`/`PUT`/`DELETE /me/events/<id>` | Eigene Veranstaltung lesen/ändern/löschen. |
| `POST /me/offers`, `GET`/`PUT`/`DELETE /me/offers/<id>` | Dasselbe für Angebote. |

Speichern liefert `{message, pending, item}`. `pending: true` heißt: wartet auf Prüfung.
Wie auf der Website müssen Änderungen an Titel, Beschreibung, Bild, Name, Logo, Titelbild,
Website oder E-Mail erneut geprüft werden.

## Admin (nur Admins, sonst 404)

`<kind>` ist `event`, `offer` oder `organization`.

| Methode & Pfad | Inhalt |
|---|---|
| `GET /admin/overview` | Zahlen, offene Prüfungen, Aufrufe der letzten Tage, Top-Veranstaltungen, letzte Aktionen. |
| `GET /admin/queue?kind=` | Warteschlange + Vorlagen für Ablehnungsgründe. |
| `POST /admin/<kind>/<id>/approve` | Freigeben (Mail an den Besitzer). |
| `POST /admin/<kind>/<id>/reject` | `reason` → Ablehnen (Mail mit Grund). |
| `POST /admin/<kind>/<id>/feature` | Tipp an/aus (nicht für Profile). |
| `POST /admin/organization/<id>/premium` | `until?` oder `action: "off"`. |
| `GET`/`PUT`/`DELETE /admin/<kind>/<id>` | Lesen, bearbeiten (Status bleibt), löschen. |
| `GET /admin/content/<kind>?status=&q=` | Alle Inhalte durchsuchen. |
| `GET /admin/users?q=` | Benutzer. |
| `POST /admin/users/<id>/block` | Sperren/entsperren (meldet sofort aus der App ab). |
| `DELETE /admin/users/<id>` | Benutzer mit allen Inhalten löschen. |
| `GET`/`POST /admin/categories`, `PUT`/`DELETE /admin/categories/<id>` | Kategorien. |
| `GET /admin/log` | Protokoll aller Admin-Aktionen. |

## Beispiel

```bash
curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"du@example.com","password":"…","device":"iPhone"}'

curl -s http://localhost:5000/api/v1/me/overview -H "Authorization: Bearer <token>"
```
