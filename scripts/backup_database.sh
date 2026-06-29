#!/usr/bin/env bash
# Dump MySQL database to database/{dbname}_{YYYY-MM-DD_HH-MM-SS}.sql
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
BACKUP_DIR="${ROOT_DIR}/database"
RETENTION_COUNT="${BACKUP_RETENTION_COUNT:-15}"
LOG_FILE="${BACKUP_DIR}/backup.log"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing .env at ${ENV_FILE}" >&2
  exit 1
fi

# Load DB settings from .env (ignore comments and Windows CRLF).
while IFS='=' read -r key value; do
  case "$key" in
    DB_DATABASE|DB_USERNAME|DB_PASSWORD|DB_HOST|DB_PORT)
      value="${value%$'\r'}"
      value="${value%\"}"
      value="${value#\"}"
      export "$key=$value"
      ;;
  esac
done < <(grep -E '^(DB_DATABASE|DB_USERNAME|DB_PASSWORD|DB_HOST|DB_PORT)=' "$ENV_FILE")

: "${DB_DATABASE:?DB_DATABASE not set in .env}"
: "${DB_USERNAME:?DB_USERNAME not set in .env}"
: "${DB_PASSWORD:?DB_PASSWORD not set in .env}"

DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3306}"

mkdir -p "$BACKUP_DIR"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"
OUTPUT_FILE="${BACKUP_DIR}/${DB_DATABASE}_${TIMESTAMP}.sql"

{
  echo "[$(date -Is)] Starting backup for ${DB_DATABASE}"
  mysqldump \
    -h "$DB_HOST" \
    -P "$DB_PORT" \
    -u "$DB_USERNAME" \
    -p"$DB_PASSWORD" \
    --single-transaction \
    --routines \
    --triggers \
    --databases "$DB_DATABASE" \
    > "$OUTPUT_FILE"
  echo "[$(date -Is)] Backup saved: ${OUTPUT_FILE} ($(du -h "$OUTPUT_FILE" | awk '{print $1}'))"
} >>"$LOG_FILE" 2>&1

# Keep only the newest N backup files for this database.
mapfile -t OLD_FILES < <(ls -1t "${BACKUP_DIR}/${DB_DATABASE}"_*.sql 2>/dev/null | tail -n +"$((RETENTION_COUNT + 1))" || true)
if ((${#OLD_FILES[@]} > 0)); then
  rm -f "${OLD_FILES[@]}"
  echo "[$(date -Is)] Pruned ${#OLD_FILES[@]} old backup(s)" >>"$LOG_FILE"
fi

echo "$OUTPUT_FILE"
