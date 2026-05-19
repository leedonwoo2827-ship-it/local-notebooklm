"""슬라이드 자료(=카드뉴스) 산출물.

lecture-postpro-mcp 의 make_cardnews() 가 그대로 import해서 쓸 수 있도록
`make_slides_lite()` 를 Streamlit/RAG 비의존 순수 async 함수로 분리해 둔다.
"""
from __future__ import annotations

import json
import re
from typing import Awaitable, Callable, Literal

from core.llm_client import get_llm_func
from core.ingest.subtitle import parse_subtitle_text

from ._base import ArtifactMeta, ArtifactResult, load_prompt

META = ArtifactMeta(
    key="slides",
    title="슬라이드 자료",
    icon="🎴",
    order=20,
    model_profile="creative",
    accepts=("subtitle", "text"),
    description="자막/텍스트 → 6슬라이드 JSON+Markdown (lecture-postpro-mcp 재사용 핵심).",
)


LLMFunc = Callable[..., Awaitable[str]]


def _strip_fence(text: str) -> str:
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    return (m.group(1) if m else text).strip()


def _to_markdown(bundle: dict) -> str:
    lines: list[str] = []
    for i, slide in enumerate(bundle.get("slides", []), 1):
        lines.append(f"## {i}. {slide.get('title','')}")
        lines.append("")
        lines.append(slide.get("body", "").strip())
        kws = slide.get("keywords") or []
        if kws:
            lines.append("")
            lines.append("**키워드**: " + ", ".join(kws))
        hint = slide.get("image_hint")
        if hint:
            lines.append("")
            lines.append(f"_이미지 힌트_: {hint}")
        lines.append("")
    return "\n".join(lines).strip()


async def make_slides_lite(
    subtitle_text: str,
    subtitle_format: Literal["srt", "vtt", "plain"] = "plain",
    metadata: dict | None = None,
    llm_call: LLMFunc | None = None,
    slides: int = 6,
) -> dict:
    """Pure async function — reused by lecture-postpro-mcp.

    Returns: {"slides":[{title, body, keywords, image_hint}], "markdown": "..."}
    """
    clean = (
        parse_subtitle_text(subtitle_text, subtitle_format)
        if subtitle_format in ("srt", "vtt")
        else subtitle_text
    )

    prompt_tpl = load_prompt("slides") or (
        "다음 강의 자막을 바탕으로 {{N}}개의 슬라이드로 정리하라. "
        "각 슬라이드는 title/body/keywords/image_hint 키를 가진 JSON. "
        "최상위는 {\"slides\": [...]} 형태."
    )
    prompt = (
        prompt_tpl.replace("{{N}}", str(slides))
        + "\n\n[메타데이터]\n"
        + json.dumps(metadata or {}, ensure_ascii=False)
        + "\n\n[자막]\n"
        + clean
    )

    caller = llm_call or get_llm_func("creative")
    raw = await caller(prompt)
    payload = _strip_fence(raw)
    try:
        bundle = json.loads(payload)
    except json.JSONDecodeError:
        bundle = {"slides": [{"title": "파싱 실패", "body": raw, "keywords": [], "image_hint": ""}]}

    bundle.setdefault("slides", [])
    bundle["markdown"] = _to_markdown(bundle)
    return bundle


async def generate(rag, context: dict) -> ArtifactResult:
    """Studio entrypoint. context expects {'subtitle_text', 'subtitle_format', 'metadata'}."""
    subtitle_text = context.get("subtitle_text") or ""
    if not subtitle_text:
        # 노트북 전체에서 자막류 소스를 끌어모은다(폴백)
        from lightrag.base import QueryParam
        subtitle_text = await rag.aquery(
            "자막/대본 내용을 그대로 긴 문장으로 다시 출력하라. 요약 금지.",
            param=QueryParam(mode="hybrid", top_k=20),
        )

    bundle = await make_slides_lite(
        subtitle_text=subtitle_text,
        subtitle_format=context.get("subtitle_format", "plain"),
        metadata=context.get("metadata"),
        slides=int(context.get("slides", 6)),
    )

    return ArtifactResult(
        key=META.key,
        title=META.title,
        markdown=bundle.get("markdown", ""),
        data=bundle,
    )
