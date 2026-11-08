#!/usr/bin/env bash
# Daily backup of database + uploads. Run by deploy/amberg-live-backup.timer (03:30).
# Keeps the last $KEEP_DAYS days locally. Copy the folder off the server as well
# (Hetzner Storage Box, rsync, restic …) – a backup on the same disk is not enough.
set -euo pipefail

APP_DIR="${APP_DIR:-/srv/amberg-live}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/amberg-live}"
KEEP_DAYS="${KEEP_DAYS:-14}"
STAMP="$(date +%Y-%m-%d_%H%M)"
TARGET="$BACKUP_DIR/$STAMP"

# Read DATABASE_URL from the app's .env (without executing the file).
DATABASE_URL="$(grep -E '^DATABASE_URL=' "$APP_DIR/.env" | cut -d= -f2- || true)"

mkdir -p "$TARGET"
chmod 700 "$BACKUP_DIR"

if [[ "$DATABASE_URL" == postgres* ]]; then
    # pg_dump wants postgresql://; strip a "+psycopg" driver suffix if present
    pg_dump --no-owner --format=custom --file="$TARGET/database.dump" "${DATABASE_URL/+psycopg/}"
else
    # SQLite: the .backup command makes a consistent copy even while the app is running
    sqlite3 "$APP_DIR/instance/amberg_live.db" ".backup '$TARGET/amberg_live.db'"
fi

tar -C "$APP_DIR/instance" -czf "$TARGET/uploads.tar.gz" uploads
cp "$APP_DIR/.env" "$TARGET/env.backup" && chmod 600 "$TARGET/env.backup"

# Remove old backups
find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -mtime +"$KEEP_DAYS" -exec rm -rf {} +

echo "Backup written to $TARGET ($(du -sh "$TARGET" | cut -f1))"
