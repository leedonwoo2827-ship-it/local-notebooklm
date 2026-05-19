"""Local sentence-transformers embedding wrapped as LightRAG EmbeddingFunc.

LiteLLM 프록시 카탈로그에 임베딩 모델이 없어서 로컬 BGE-M3로 고정한다.
4070 8GB에서 LLM과 동시 점유 시 OOM 위험이 있으면 EMBED_DEVICE=cpu로 강제 가능.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
from lightrag.utils import EmbeddingFunc
from sentence_transformers import SentenceTransformer

from .settings import SETTINGS


def _resolve_device() -> str:
    if SETTINGS.embed_device != "auto":
        return SETTINGS.embed_device
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    return SentenceTransformer(SETTINGS.embed_model, device=_resolve_device())


@lru_cache(maxsize=1)
def get_embedding_func() -> EmbeddingFunc:
    model = _load_model()
    dim = model.get_sentence_embedding_dimension()

    async def _embed(texts: list[str]) -> np.ndarray:
        vecs = model.encode(
            texts,
            batch_size=16,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return vecs.astype(np.float32)

    return EmbeddingFunc(
        embedding_dim=dim,
        max_token_size=8192,
        func=_embed,
    )
