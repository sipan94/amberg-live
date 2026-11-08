# Deployment auf einem kleinen Linux-Server (z. B. Hetzner)

Diese Anleitung bringt Amberg Live auf einen eigenen Server mit **Ubuntu 24.04**:
gunicorn (App) → nginx (Webserver, HTTPS) → Let's Encrypt (Zertifikat) → systemd (Autostart) → tägliches Backup.
Zeitaufwand: ca. 1 Stunde. Alle Befehle als `root` bzw. mit `sudo`, außer wo `amberg` steht.

> Platzhalter: `amberg-live.de` = deine Domain, `DEINE-IP` = IPv4 des Servers.

---

## 1. Server anlegen

1. Bei Hetzner Cloud einen Server erstellen: **CX22** (2 vCPU, 4 GB) reicht völlig, Standort Nürnberg oder Falkenstein (Daten bleiben in Deutschland), Image **Ubuntu 24.04**, deinen **SSH-Key** hinterlegen.
2. Beim Domain-Anbieter DNS-Einträge setzen: `A amberg-live.de → DEINE-IP` und `A www → DEINE-IP` (bei IPv6 zusätzlich `AAAA`).
3. Einloggen: `ssh root@DEINE-IP`

## 2. Grundsicherung

```bash
apt update && apt full-upgrade -y
apt install -y ufw fail2ban unattended-upgrades
ufw allow OpenSSH && ufw allow "Nginx Full" 2>/dev/null || ufw allow 80,443/tcp
ufw --force enable
dpkg-reconfigure -plow unattended-upgrades     # automatische Sicherheitsupdates: "Yes"
timedatectl set-timezone Europe/Berlin
```

Optional, empfohlen: in `/etc/ssh/sshd_config` `PasswordAuthentication no` setzen und `systemctl restart ssh`.

## 3. Pakete und Benutzer

```bash
apt install -y python3 python3-venv python3-dev build-essential nginx certbot python3-certbot-nginx sqlite3 git
adduser --system --group --no-create-home --home /srv/amberg-live amberg
install -d -o amberg -g amberg /srv/amberg-live
```

Ubuntu 24.04 bringt Python 3.12 mit – passt.

## 4. Datenbank: PostgreSQL (empfohlen)

SQLite funktioniert für den Start, PostgreSQL ist robuster bei vielen gleichzeitigen Zugriffen.

```bash
apt install -y postgresql
sudo -u postgres createuser amberg
sudo -u postgres createdb -O amberg amberg_live
sudo -u postgres psql -c "ALTER USER amberg PASSWORD 'EIN-LANGES-PASSWORT';"
```

→ in `.env`: `DATABASE_URL=postgresql://amberg:EIN-LANGES-PASSWORT@localhost/amberg_live`

(Für SQLite einfach `DATABASE_URL` leer lassen und diesen Schritt überspringen.)

## 5. Code auf den Server bringen

Per Git (empfohlen, wenn das Projekt in einem Repository liegt):

```bash
sudo -u amberg git clone https://github.com/DEIN-NAME/amberg-live.git /srv/amberg-live
```

…oder vom eigenen Rechner kopieren (ohne `.venv`, `node_modules`, `instance`, `.env`):

```bash
rsync -av --exclude .venv --exclude node_modules --exclude instance --exclude .env ./ root@DEINE-IP:/srv/amberg-live/
chown -R amberg:amberg /srv/amberg-live
```

In beiden Fällen liegt der Code danach direkt in `/srv/amberg-live`.

## 6. Python-Umgebung und Konfiguration

```bash
cd /srv/amberg-live
sudo -u amberg python3 -m venv .venv
sudo -u amberg .venv/bin/pip install -r requirements.txt "psycopg[binary]~=3.2"
sudo -u amberg cp .env.example .env
sudo -u amberg nano .env
chmod 600 .env
```

In `.env` mindestens setzen:

```ini
APP_ENV=production
SECRET_KEY=…            # python3 -c "import secrets; print(secrets.token_hex(32))"
SITE_URL=https://amberg-live.de
DATABASE_URL=postgresql://amberg:…@localhost/amberg_live
ALLOWED_HOSTS=amberg-live.de,www.amberg-live.de
PROXY_COUNT=1
ADMIN_EMAIL=deine@adresse.de
MAIL_HOST=smtp.dein-anbieter.de
MAIL_PORT=587
MAIL_USERNAME=…
MAIL_PASSWORD=…
MAIL_FROM=Amberg Live <noreply@amberg-live.de>
```

Datenbank einrichten und Admin anlegen:

```bash
cd /srv/amberg-live
sudo -u amberg .venv/bin/flask --app wsgi:app db upgrade
sudo -u amberg .venv/bin/flask --app wsgi:app seed-categories
sudo -u amberg .venv/bin/flask --app wsgi:app create-admin deine@adresse.de
```

> `flask seed` (Demo-Daten) verweigert in Produktion bewusst den Dienst.

## 7. App als Dienst starten (systemd)

```bash
cp deploy/amberg-live.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now amberg-live
systemctl status amberg-live          # sollte "active (running)" zeigen
curl -s http://127.0.0.1:8000/healthz  # {"status":"ok"}
```

## 8. nginx und HTTPS

```bash
mkdir -p /var/www/certbot
# zuerst nur HTTP, damit certbot das Zertifikat holen kann:
cat > /etc/nginx/sites-available/amberg-live <<'EOF'
server { listen 80; server_name amberg-live.de www.amberg-live.de;
  location /.well-known/acme-challenge/ { root /var/www/certbot; }
  location / { proxy_pass http://127.0.0.1:8000; include proxy_params; } }
EOF
ln -sf /etc/nginx/sites-available/amberg-live /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

certbot certonly --webroot -w /var/www/certbot -d amberg-live.de -d www.amberg-live.de \
  --email deine@adresse.de --agree-tos --no-eff-email

# jetzt die vollständige Konfiguration mit HTTPS:
cp deploy/nginx.conf /etc/nginx/sites-available/amberg-live
sed -i 's/amberg-live.de/DEINE-DOMAIN.de/g' /etc/nginx/sites-available/amberg-live   # falls andere Domain
nginx -t && systemctl reload nginx
```

Zertifikate erneuert certbot automatisch (`systemctl list-timers | grep certbot`).
Test: <https://amberg-live.de> aufrufen, dann z. B. <https://securityheaders.com> und
<https://www.ssllabs.com/ssltest/> prüfen.

## 9. Tägliches Backup

```bash
chmod +x deploy/backup.sh
cp deploy/amberg-live-backup.service deploy/amberg-live-backup.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now amberg-live-backup.timer
systemctl start amberg-live-backup.service    # einmal sofort testen
ls -lh /var/backups/amberg-live/
```

Das Backup (03:30 Uhr) enthält Datenbank, Uploads und `.env`; 14 Tage werden behalten. Der Timer beendet
dabei auch abgelaufene Premium-Einträge. **Wichtig:** Backups zusätzlich außerhalb des Servers ablegen, z. B.
Hetzner Storage Box:

```bash
# einmalig: SSH-Key für die Storage Box hinterlegen, dann z. B. per Cron nach dem Backup:
rsync -az --delete /var/backups/amberg-live/ u12345@u12345.your-storagebox.de:amberg-live/
```

### Wiederherstellen

```bash
systemctl stop amberg-live
# PostgreSQL:
sudo -u postgres pg_restore --clean --no-owner -d amberg_live /var/backups/amberg-live/DATUM/database.dump
# oder SQLite:
cp /var/backups/amberg-live/DATUM/amberg_live.db /srv/amberg-live/instance/amberg_live.db
# Uploads:
tar -C /srv/amberg-live/instance -xzf /var/backups/amberg-live/DATUM/uploads.tar.gz
chown -R amberg:amberg /srv/amberg-live/instance
systemctl start amberg-live
```

## 10. Updates einspielen

```bash
cd /srv/amberg-live
sudo -u amberg git pull                      # bzw. neue Dateien per rsync kopieren
sudo -u amberg .venv/bin/pip install -r requirements.txt
sudo -u amberg .venv/bin/flask --app wsgi:app db upgrade
systemctl restart amberg-live
```

Vorher lokal `pytest` laufen lassen. CSS/Icons werden lokal gebaut und mit dem Code übertragen.

## 11. Logs und Fehlersuche

```bash
journalctl -u amberg-live -f                       # App-Log live
tail -f /srv/amberg-live/instance/logs/amberg_live.log
tail -f /var/log/nginx/amberg-live.error.log
systemctl status amberg-live nginx
```

| Problem | Lösung |
|---|---|
| `502 Bad Gateway` | App läuft nicht: `journalctl -u amberg-live -n 50` |
| „Set a strong SECRET_KEY“ | `SECRET_KEY` in `.env` fehlt oder ist zu kurz |
| `400 Bad Request` bei allen Seiten | Domain fehlt in `ALLOWED_HOSTS` |
| Bilder fehlen | Rechte prüfen: `chown -R amberg:amberg /srv/amberg-live/instance` |
| Keine E-Mails | `MAIL_*` prüfen; Fehler stehen im App-Log |

## Alternative: Docker

```bash
cp .env.example .env    # APP_ENV=production, SECRET_KEY, SITE_URL … setzen
docker compose up -d --build
docker compose exec app flask --app wsgi:app create-admin deine@adresse.de
```

Die App lauscht dann auf `127.0.0.1:8000`; davor wie in Schritt 8 nginx mit HTTPS setzen
(den `/static/`- und `/uploads/`-Block durch `proxy_pass` ersetzen oder das Volume nach außen mounten).
Daten liegen im Volume `amberg_data` – im Backup-Skript dann `APP_DIR` entsprechend anpassen
bzw. `docker compose exec app sqlite3 …`/`pg_dump` verwenden.

## Checkliste vor dem Start

- [ ] Alle `TODO` in Impressum, Datenschutz, AGB, Kontakt ausgefüllt und rechtlich geprüft
- [ ] Auftragsverarbeitungsverträge mit Hoster und E-Mail-Anbieter abgeschlossen
- [ ] `APP_ENV=production`, starker `SECRET_KEY`, `ALLOWED_HOSTS` gesetzt
- [ ] Admin-Konto mit langem Passwort angelegt
- [ ] E-Mail-Versand getestet (Registrierung mit eigener Adresse)
- [ ] Backup läuft und liegt zusätzlich außerhalb des Servers; Wiederherstellung einmal geprobt
- [ ] OpenStreetMap-Kachelnutzung: Bei viel Verkehr einen eigenen/kommerziellen Kachel-Anbieter nutzen
      (Nutzungsrichtlinie der OSMF beachten) und Datenschutzerklärung anpassen
