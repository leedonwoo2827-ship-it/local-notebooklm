#!/usr/bin/env bash
# Local NotebookLM - macOS / Linux run
set -e

cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
    echo "[ERROR] Virtual environment (.venv) not found."
    echo "        Run ./setup.sh first."
    exit 1
fi

[ -f ".env" ] || cp .env.example .env

echo "Starting Local NotebookLM... your browser will open automatically."
echo "To stop: press Ctrl+C in this window."
echo

# shellcheck disable=SC1091
source .venv/bin/activate
streamlit run app.py
