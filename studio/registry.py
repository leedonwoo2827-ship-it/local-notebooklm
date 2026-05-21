"""Studio plugin discovery.

`studio/*.py`를 import하면서 모듈에 `META: ArtifactMeta`가 있는 것만 등록한다.
파일명이 META.key 와 다를 경우 META.key 가 우선.
"""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from types import ModuleType

from ._base import ArtifactMeta


@dataclass(frozen=True)
class RegisteredArtifact:
    meta: ArtifactMeta
    module: ModuleType

    async def generate(self, rag, context: dict):
        return await self.module.generate(rag, context)

    def render(self, result) -> None:
        renderer = getattr(self.module, "render", None)
        if renderer is None:
            import streamlit as st
            st.markdown(result.markdown or "_(빈 결과)_")
            return
        renderer(result)


def discover() -> list[RegisteredArtifact]:
    import os
    import studio as pkg

    visible_env = os.environ.get("STUDIO_VISIBLE", "").strip()
    visible_keys = {k.strip() for k in visible_env.split(",") if k.strip()}

    found: list[RegisteredArtifact] = []
    for info in pkgutil.iter_modules(pkg.__path__):
        name = info.name
        if name.startswith("_") or name in {"registry"}:
            continue
        module = importlib.import_module(f"studio.{name}")
        meta = getattr(module, "META", None)
        if not isinstance(meta, ArtifactMeta):
            continue
        if not hasattr(module, "generate"):
            continue
        # hidden 산출물은 STUDIO_VISIBLE 환경변수에 명시될 때만 노출
        if meta.hidden and meta.key not in visible_keys:
            continue
        found.append(RegisteredArtifact(meta=meta, module=module))

    found.sort(key=lambda r: (r.meta.order, r.meta.key))
    return found
