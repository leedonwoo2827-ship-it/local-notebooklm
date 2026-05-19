"""SRT/VTT 자막 → 타임코드 제거된 plain text.

PDF 계획서의 클로드 조율 팁: "자막 파일 분석 시 타임코드([00:01:23])를 제거하고
문맥을 이어붙이는 전처리 필터를 반드시 포함하라" — 카드뉴스/요약 품질의 핵심.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal


SubtitleFormat = Literal["srt", "vtt", "auto"]

_TIMECODE_INLINE = re.compile(r"\[\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\]")


def detect_format(path: Path) -> Literal["srt", "vtt"]:
    suffix = path.suffix.lower().lstrip(".")
    if suffix in ("srt", "vtt"):
        return suffix  # type: ignore[return-value]
    head = path.read_text(encoding="utf-8", errors="ignore")[:200]
    if "WEBVTT" in head:
        return "vtt"
    return "srt"


def _parse_srt(text: str) -> list[str]:
    import srt
    return [c.content.replace("\n", " ").strip() for c in srt.parse(text)]


def _parse_vtt(text: str) -> list[str]:
    import webvtt
    import io
    cues = list(webvtt.read_buffer(io.StringIO(text)))
    return [c.text.replace("\n", " ").strip() for c in cues]


def _dedup_adjacent(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        if not line:
            continue
        if out and out[-1] == line:
            continue
        out.append(line)
    return out


def parse_subtitle(path: Path, fmt: SubtitleFormat = "auto") -> str:
    """Read a subtitle file and return timecode-stripped plain text."""
    real_fmt = detect_format(path) if fmt == "auto" else fmt
    raw = path.read_text(encoding="utf-8", errors="ignore")
    lines = _parse_vtt(raw) if real_fmt == "vtt" else _parse_srt(raw)
    lines = [_TIMECODE_INLINE.sub("", l).strip() for l in lines]
    lines = _dedup_adjacent(lines)
    return " ".join(lines)


def parse_subtitle_text(text: str, fmt: Literal["srt", "vtt"]) -> str:
    """Same as parse_subtitle but accepts raw string (used by Studio slides)."""
    lines = _parse_vtt(text) if fmt == "vtt" else _parse_srt(text)
    lines = [_TIMECODE_INLINE.sub("", l).strip() for l in lines]
    return " ".join(_dedup_adjacent(lines))
