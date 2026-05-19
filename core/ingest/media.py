"""MP4 → STT → text source.

영상은 직접 인덱싱하지 않고, faster-whisper(또는 LiteLLM)로 자막을 뽑아
plain text(.transcript.txt)로 변환한 뒤 RAG-Anything에 인입한다.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from ..stt import transcribe


async def media_to_text(media_path: Path, out_dir: Path) -> Path:
    """Return path to .transcript.txt next to the original media file."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / (media_path.stem + ".transcript.txt")

    if out_path.exists() and out_path.stat().st_mtime >= media_path.stat().st_mtime:
        return out_path

    transcript = await transcribe(media_path)
    out_path.write_text(transcript.plain(), encoding="utf-8")
    return out_path


def is_media(path: Path) -> bool:
    return path.suffix.lower() in {".mp4", ".m4a", ".mp3", ".wav", ".webm", ".mov"}
