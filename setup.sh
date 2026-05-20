#!/usr/bin/env bash
# Local NotebookLM - macOS / Linux setup
set -e

cd "$(dirname "$0")"

echo "============================================================"
echo "  Local NotebookLM - Setup (macOS / Linux)"
echo "============================================================"
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 not found."
    echo "        macOS:   brew install python@3.11"
    echo "        Ubuntu:  sudo apt install python3.11 python3.11-venv"
    exit 1
fi

PYVER="$(python3 --version 2>&1 | awk '{print $2}')"
echo "[1/4] Python ${PYVER} detected."

if [ -d ".venv" ] && [ -x ".venv/bin/python" ]; then
    echo "[2/4] Virtual environment already exists. Skipping."
else
    echo "[2/4] Creating virtual environment (.venv) ..."
    python3 -m venv .venv
fi

echo "[3/5] Installing dependencies (may take 10-15 minutes) ..."
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
pip install -e .

echo "[4/5] Installing Playwright Chromium (for cardnews PNG capture) ..."
if ! python -m playwright install chromium; then
    echo "[WARN] Playwright Chromium install failed. Cardnews PNG capture will be disabled."
    echo "       Retry later:  .venv/bin/python -m playwright install chromium"
fi

if [ -f ".env" ]; then
    echo "[5/5] .env already exists."
else
    cp .env.example .env
    echo "[5/5] Created .env from .env.example."
fi

echo
echo "============================================================"
echo "  Setup complete. Now run:  ./run.sh"
echo "============================================================"
