"""STT — faster-whisper 로컬 우선, LiteLLM gpt-4o-transcribe 폴백.

일반 사무용 PC(GPU 없음) 호환을 위해 디바이스 자동 다운스케일링:
  - CUDA 가능 → large-v3
  - CPU only  → small
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from openai import OpenAI

from .settings import SETTINGS


@dataclass
class Transcript:
    text: str
    language: str
    segments: list[dict]  # {start, end, text}

    def plain(self) -> str:
        return self.text.strip()


def _device_and_model() -> tuple[str, str, str]:
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda", "float16", SETTINGS.whisper_model_cuda
    except Exception:
        pass
    return "cpu", "int8", SETTINGS.whisper_model_cpu


@lru_cache(maxsize=1)
def _local_model():
    from faster_whisper import WhisperModel
    device, compute, name = _device_and_model()
    return WhisperModel(name, device=device, compute_type=compute)


def _transcribe_local(media_path: Path) -> Transcript:
    model = _local_model()
    segments, info = model.transcribe(
        str(media_path),
        language=None,
        vad_filter=True,
        beam_size=5,
    )
    segs = [
        {"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments
    ]
    return Transcript(
        text=" ".join(s["text"] for s in segs),
        language=info.language,
        segments=segs,
    )


def _transcribe_litellm(media_path: Path) -> Transcript:
    client = OpenAI(
        api_key=SETTINGS.litellm_key or "missing",
        base_url=f"{SETTINGS.litellm_url.rstrip('/')}/v1",
    )
    with media_path.open("rb") as f:
        resp = client.audio.transcriptions.create(
            model=SETTINGS.stt_model_litellm,
            file=f,
            response_format="verbose_json",
        )
    segs = []
    for s in getattr(resp, "segments", []) or []:
        segs.append({"start": s.start, "end": s.end, "text": s.text.strip()})
    return Transcript(
        text=resp.text,
        language=getattr(resp, "language", "ko"),
        segments=segs,
    )


async def transcribe(media_path: Path) -> Transcript:
    """Sync libs wrapped — Streamlit이 이미 별도 thread를 잡으므로 OK."""
    if SETTINGS.whisper_backend == "litellm":
        return _transcribe_litellm(media_path)
    return _transcribe_local(media_path)
