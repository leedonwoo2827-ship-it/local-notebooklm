"""RAGAnything wrapper — 노트북 컬렉션 단위로 LightRAG working_dir 분리.

NotebookLM의 "노트북" 한 개 = 디렉터리 한 개. 인덱스/소스/산출물이 같은
부모 폴더 아래 모이도록 강제한다. 재기동 시 동일 이름으로 다시 호출하면
LightRAG가 기존 그래프/벡터를 자동 로딩한다.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from raganything import RAGAnything, RAGAnythingConfig

from .embeddings import get_embedding_func
from .llm_client import get_llm_func
from .settings import SETTINGS


def _slug(name: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in "-_." else "_" for c in name.strip())
    return cleaned or "default"


@dataclass
class NotebookPaths:
    name: str
    root: Path
    rag_storage: Path
    sources: Path
    artifacts: Path

    @classmethod
    def for_notebook(cls, name: str) -> "NotebookPaths":
        slug = _slug(name)
        root = SETTINGS.notebook_root / slug
        return cls(
            name=slug,
            root=root,
            rag_storage=root / "rag_storage",
            sources=root / "sources",
            artifacts=root / "artifacts",
        )

    def ensure(self) -> None:
        for p in (self.root, self.rag_storage, self.sources, self.artifacts):
            p.mkdir(parents=True, exist_ok=True)


_instances: dict[str, RAGAnything] = {}
_lock = asyncio.Lock()


async def build_rag(notebook_name: str) -> RAGAnything:
    """Get-or-create RAGAnything for a notebook. Idempotent."""
    paths = NotebookPaths.for_notebook(notebook_name)
    paths.ensure()

    key = paths.name
    async with _lock:
        if key in _instances:
            return _instances[key]

        config = RAGAnythingConfig(
            working_dir=str(paths.rag_storage),
            parser="mineru",
            parse_method="auto",
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
        )

        rag = RAGAnything(
            config=config,
            llm_model_func=get_llm_func("extract"),
            vision_model_func=get_llm_func("strong"),
            embedding_func=get_embedding_func(),
        )
        _instances[key] = rag
        return rag


def list_notebooks() -> list[str]:
    """Discover existing notebooks under NOTEBOOK_ROOT."""
    root = SETTINGS.notebook_root
    if not root.exists():
        return []
    return sorted(
        p.name for p in root.iterdir() if p.is_dir() and (p / "rag_storage").exists()
    )


def list_sources(notebook_name: str) -> list[Path]:
    paths = NotebookPaths.for_notebook(notebook_name)
    if not paths.sources.exists():
        return []
    return sorted(p for p in paths.sources.iterdir() if p.is_file())
