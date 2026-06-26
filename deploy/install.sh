#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/rankplex/htdocs/rankplex.cloud/htdocs/foodstock}"
REPO_URL="${REPO_URL:-https://github.com/nageshnice/foodstock.git}"
PYTHON_BIN="${PYTHON_BIN:-python3.11}"

echo "==> Food Stock API deployment"
echo "    Target: ${APP_DIR}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

if [ ! -d "${APP_DIR}/.git" ]; then
  mkdir -p "$(dirname "${APP_DIR}")"
  git clone "${REPO_URL}" "${APP_DIR}"
else
  cd "${APP_DIR}"
  git pull --ff-only origin main
fi

cd "${APP_DIR}"

if [ ! -f .env ]; then
  echo "ERROR: .env missing. Copy deploy/production.env.example to .env and fill secrets."
  exit 1
fi

"${PYTHON_BIN}" -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cd admin
npm ci
npm run build
cd ..

source .venv/bin/activate
python -m scripts.create_tables
python -m scripts.bootstrap_admin
python -m scripts.seed_catalog

echo "==> Deployment files ready. Start API with:"
echo "    cd ${APP_DIR} && source .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8010"
