from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


Backend = Literal["litellm", "ollama"]
WhisperBackend = Literal["local", "litellm"]
Profile = Literal["chat", "extract", "strong", "creative"]


@dataclass(frozen=True)
class Settings:
    llm_backend: Backend
    whisper_backend: WhisperBackend

    litellm_url: str
    litellm_key: str
    ollama_url: str
    ollama_key: str

    model_chat: str
    model_extract: str
    model_strong: str
    model_creative: str
    tts_model: str
    stt_model_litellm: str

    embed_model: str
    embed_device: str

    whisper_model_cuda: str
    whisper_model_cpu: str

    notebook_root: Path

    def model_for(self, profile: Profile) -> str:
        return {
            "chat": self.model_chat,
            "extract": self.model_extract,
            "strong": self.model_strong,
            "creative": self.model_creative,
        }[profile]

    def base_url(self) -> str:
        if self.llm_backend == "litellm":
            return f"{self.litellm_url.rstrip('/')}/v1"
        return self.ollama_url.rstrip("/")

    def api_key(self) -> str:
        if self.llm_backend == "litellm":
            return self.litellm_key or "missing"
        return self.ollama_key or "ollama"


def load() -> Settings:
    return Settings(
        llm_backend=_env("LLM_BACKEND", "litellm"),  # type: ignore[arg-type]
        whisper_backend=_env("WHISPER_BACKEND", "local"),  # type: ignore[arg-type]
        litellm_url=_env("UBION_LITELLM_URL", ""),
        litellm_key=_env("UBION_LITELLM_KEY"),
        ollama_url=_env("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        ollama_key=_env("OLLAMA_API_KEY", "ollama"),
        model_chat=_env("MODEL_CHAT", "deepseek-v4-flash"),
        model_extract=_env("MODEL_EXTRACT", "deepseek-v4-flash"),
        model_strong=_env("MODEL_STRONG", "claude-sonnet-4-6"),
        model_creative=_env("MODEL_CREATIVE", "claude-sonnet-4-6"),
        tts_model=_env("TTS_MODEL", "gpt-4o-mini-tts"),
        stt_model_litellm=_env("STT_MODEL_LITELLM", "gpt-4o-transcribe"),
        embed_model=_env("EMBED_MODEL", "BAAI/bge-m3"),
        embed_device=_env("EMBED_DEVICE", "auto"),
        whisper_model_cuda=_env("WHISPER_MODEL_CUDA", "large-v3"),
        whisper_model_cpu=_env("WHISPER_MODEL_CPU", "small"),
        notebook_root=Path(_env("NOTEBOOK_ROOT", "./data/notebooks")).resolve(),
    )


SETTINGS = load()
