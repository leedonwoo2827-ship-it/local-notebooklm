"""보고서 산출물 — 노트북 전체 소스에서 ~3,000자 종합 Markdown."""
from __future__ import annotations

from core.llm_client import get_llm_func

from ._base import ArtifactMeta, ArtifactResult, load_prompt

META = ArtifactMeta(
    key="report",
    title="보고서",
    icon="📄",
    order=10,
    model_profile="strong",
    description="노트북 전체 소스를 종합한 3,000자 Markdown 보고서.",
)


async def generate(rag, context: dict) -> ArtifactResult:
    focus = (context.get("focus") or "").strip()
    template = load_prompt(META.key)
    instruction = template.replace("{{FOCUS}}", focus or "전체 핵심 종합")

    answer = await rag.aquery(
        instruction,
        mode="hybrid",
        top_k=40,
        response_type="Multi-section Markdown",
    )

    return ArtifactResult(
        key=META.key,
        title=META.title,
        markdown=answer or "_(빈 응답)_",
        data={"focus": focus},
    )
