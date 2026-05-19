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

echo "[3/4] Installing dependencies (may take 10-15 minutes) ..."
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
pip install -e .

if [ -f ".env" ]; then
    echo "[4/4] .env already exists."
else
    cp .env.example .env
    echo "[4/4] Created .env from .env.example."
fi

echo
echo "============================================================"
echo "  Setup complete. Now run:  ./run.sh"
echo "============================================================"
