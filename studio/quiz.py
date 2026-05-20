"""퀴즈 산출물 — 객관식 문항 + 정답 + 해설."""
from __future__ import annotations

import json
import re

from ._base import ArtifactMeta, ArtifactResult, load_prompt

META = ArtifactMeta(
    key="quiz",
    title="퀴즈",
    icon="❓",
    order=50,
    model_profile="strong",
    description="4지선다 객관식 + 정답 + 해설.",
)


def _strip_fence(text: str) -> str:
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    return (m.group(1) if m else text).strip()


def _to_markdown(questions: list[dict]) -> str:
    out = []
    for i, q in enumerate(questions, 1):
        out.append(f"### Q{i}. {q.get('question', '')}")
        for idx, choice in enumerate(q.get("choices", []), 1):
            out.append(f"{idx}. {choice}")
        out.append("")
        out.append(f"<details><summary>정답·해설</summary>\n\n"
                   f"**정답**: {q.get('answer','?')}\n\n"
                   f"**해설**: {q.get('rationale','')}\n\n</details>")
        out.append("")
    return "\n".join(out).strip()


async def generate(rag, context: dict) -> ArtifactResult:
    count = int(context.get("count", 10))
    instruction = load_prompt(META.key) or (
        f"노트북 핵심에서 4지선다 문제 {count}개를 출제하라. "
        "각 항목 키: question, choices(4개), answer(1~4), rationale. "
        "최상위는 {\"questions\": [...]} JSON. JSON 외 텍스트 금지."
    )
    raw = await rag.aquery(
        instruction.replace("{{N}}", str(count)),
        mode="hybrid",
        top_k=30,
    )
    try:
        bundle = json.loads(_strip_fence(raw))
        questions = bundle.get("questions", []) if isinstance(bundle, dict) else bundle
    except json.JSONDecodeError:
        questions = []

    return ArtifactResult(
        key=META.key,
        title=META.title,
        markdown=_to_markdown(questions) or "_(문항 생성 실패)_",
        data={"questions": questions},
    )
