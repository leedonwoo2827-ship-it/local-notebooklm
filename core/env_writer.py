"""Persist key/value pairs to the project .env file.

In-app key entry 화면이 입력값을 받아 이 모듈로 .env를 갱신한다.
- 기존 키가 있으면 그 라인만 교체
- 없으면 파일 끝에 추가
- 주석/공백 라인은 보존
"""
from __future__ import annotations

import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _ROOT / ".env"


def env_path() -> Path:
    return _ENV_PATH


def update_env(values: dict[str, str]) -> None:
    """Upsert each (key, value) into .env. Creates the file if missing."""
    _ENV_PATH.touch(exist_ok=True)
    lines = _ENV_PATH.read_text(encoding="utf-8").splitlines()
    keys_left = dict(values)

    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            out.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in keys_left:
            out.append(f"{key}={keys_left.pop(key)}")
        else:
            out.append(line)

    for k, v in keys_left.items():
        out.append(f"{k}={v}")

    _ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")

    # 현재 프로세스에도 즉시 반영
    for k, v in values.items():
        os.environ[k] = v
