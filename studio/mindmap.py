"""마인드맵 산출물 — LightRAG 응답을 Mermaid mindmap 문법으로 직렬화."""
from __future__ import annotations

import re

from lightrag.base import QueryParam

from ._base import ArtifactMeta, ArtifactResult, load_prompt

META = ArtifactMeta(
    key="mindmap",
    title="마인드맵",
    icon="🧠",
    order=30,
    model_profile="strong",
    description="LightRAG 지식 그래프 기반 Mermaid mindmap.",
)


def _to_mermaid_codeblock(raw: str) -> str:
    text = raw.strip()
    # LLM이 이미 mermaid 펜스를 두른 경우 그대로 사용
    m = re.search(r"```mermaid\s*([\s\S]+?)```", text)
    body = (m.group(1) if m else text).strip()
    if not body.lower().startswith("mindmap"):
        body = "mindmap\n  root((핵심))\n    " + body.replace("\n", "\n    ")
    return f"```mermaid\n{body}\n```"


async def generate(rag, context: dict) -> ArtifactResult:
    instruction = load_prompt(META.key) or (
        "노트북 전체 핵심 개념을 mermaid mindmap 문법으로만 출력하라. "
        "최소 20개 노드, 3단계 이상 분기. ```mermaid 펜스 포함."
    )
    answer = await rag.aquery(
        instruction,
        param=QueryParam(mode="hybrid", top_k=30),
    )
    return ArtifactResult(
        key=META.key,
        title=META.title,
        markdown=_to_mermaid_codeblock(answer or "root((빈 결과))"),
    )
