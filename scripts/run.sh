#!/usr/bin/env bash
# Local NotebookLM - macOS / Linux 실행 스크립트
set -e

cd "$(dirname "$0")/.."

if [ ! -x ".venv/bin/python" ]; then
    echo "[에러] 가상환경(.venv)이 없습니다. 먼저 ./setup.sh 를 실행하세요."
    exit 1
fi

[ -f ".env" ] || cp .env.example .env

echo "Local NotebookLM 실행 중... (브라우저가 자동으로 열립니다)"
echo "종료: 이 창에서 Ctrl+C"
echo

# shellcheck disable=SC1091
source .venv/bin/activate
streamlit run app.py
