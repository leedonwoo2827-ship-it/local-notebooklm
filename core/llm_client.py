"""LLM call adapters wired to LightRAG's openai_complete_if_cache.

Profile → model 매핑은 settings.py에서 결정한다. base_url/api_key는
LLM_BACKEND 환경변수(litellm | ollama)로 토글된다.

LightRAG가 기대하는 비동기 시그니처:
    async def func(prompt, system_prompt=None, history_messages=[], **kwargs) -> str
"""
from __future__ import annotations

from functools import lru_cache
from typing import Awaitable, Callable

from lightrag.llm.openai import openai_complete_if_cache

from .settings import SETTINGS, Profile

LLMFunc = Callable[..., Awaitable[str]]


def _make_llm(model: str) -> LLMFunc:
    base_url = SETTINGS.base_url()
    api_key = SETTINGS.api_key()

    async def _call(prompt, system_prompt=None, history_messages=None, **kwargs):
        return await openai_complete_if_cache(
            model,
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages or [],
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )

    _call.__name__ = f"llm_{model.replace('-', '_')}"
    return _call


@lru_cache(maxsize=8)
def get_llm_func(profile: Profile = "chat") -> LLMFunc:
    """Profile-based LLM caller. Cached per profile so RAGAnything reuses the same closure."""
    return _make_llm(SETTINGS.model_for(profile))


@lru_cache(maxsize=8)
def get_llm_func_for_model(model: str) -> LLMFunc:
    """Direct model override (for Studio artifacts that pin a specific model)."""
    return _make_llm(model)
