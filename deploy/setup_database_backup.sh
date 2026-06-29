#!/usr/bin/env bash
# Install cron job: MySQL dump every 2 days at 03:00 server time.
set -euo pipefail

APP_DIR="${APP_DIR:-/home/rankplex/htdocs/rankplex.cloud/htdocs/foodstock}"
CRON_TAG="# foodstock-db-backup"
CRON_LINE="0 3 */2 * * cd ${APP_DIR} && /bin/bash scripts/backup_database.sh >> database/backup.log 2>&1 ${CRON_TAG}"

chmod +x "${APP_DIR}/scripts/backup_database.sh"
mkdir -p "${APP_DIR}/database"

CURRENT_CRON="$(crontab -l 2>/dev/null || true)"
if echo "$CURRENT_CRON" | grep -Fq "$CRON_TAG"; then
  echo "Cron entry already installed."
else
  {
    echo "$CURRENT_CRON" | sed '/^$/d'
    echo "$CRON_LINE"
  } | crontab -
  echo "Installed cron: ${CRON_LINE}"
fi

echo "Running initial backup..."
cd "$APP_DIR"
bash scripts/backup_database.sh
