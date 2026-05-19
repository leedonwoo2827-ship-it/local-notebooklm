#!/usr/bin/env bash
# Local NotebookLM - macOS / Linux 설치 스크립트
set -e

cd "$(dirname "$0")/.."

echo "============================================================"
echo "  Local NotebookLM - 설치 스크립트 (macOS / Linux)"
echo "============================================================"
echo

# 1) Python 확인
if ! command -v python3 >/dev/null 2>&1; then
    echo "[에러] python3 가 설치되어 있지 않습니다."
    echo "       macOS:   brew install python@3.11"
    echo "       Ubuntu:  sudo apt install python3.11 python3.11-venv"
    exit 1
fi

PYVER="$(python3 --version 2>&1 | awk '{print $2}')"
echo "[1/4] Python ${PYVER} 확인 완료"

# 2) venv
if [ -d ".venv" ] && [ -x ".venv/bin/python" ]; then
    echo "[2/4] 가상환경(.venv)이 이미 존재합니다. 건너뜀."
else
    echo "[2/4] 가상환경 생성 중..."
    python3 -m venv .venv
fi

# 3) 의존성
echo "[3/4] 의존성 설치 중 (10~15분 소요)..."
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
pip install -e .

# 4) .env
if [ -f ".env" ]; then
    echo "[4/4] .env 파일이 이미 존재합니다."
else
    cp .env.example .env
    echo "[4/4] .env 파일 생성 완료. (앱 첫 실행 시 화면에서 URL/키 입력)"
fi

echo
echo "============================================================"
echo "  설치 완료. 이제 ./run.sh 를 실행하세요."
echo "============================================================"
