"""퀴즈 산출물 — 객관식 문항 + 정답 + 해설 (markdown + .xlsx)."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from ._base import ArtifactMeta, ArtifactResult, load_prompt
from ._xlsx import write_table_xlsx

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


def _to_xlsx_rows(questions: list[dict]) -> list[list]:
    rows: list[list] = []
    for i, q in enumerate(questions, 1):
        choices = q.get("choices", []) + ["", "", "", ""]  # 부족하면 빈칸 채움
        rows.append([
            i,
            q.get("question", ""),
            choices[0], choices[1], choices[2], choices[3],
            q.get("answer", ""),
            q.get("rationale", ""),
        ])
    return rows


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

    files: list[Path] = []
    artifacts_dir = context.get("artifacts_dir")
    if artifacts_dir and questions:
        out_dir = Path(artifacts_dir) / META.key
        try:
            xlsx_path = write_table_xlsx(
                out_dir / f"quiz_{int(time.time())}.xlsx",
                headers=["#", "문제", "보기1", "보기2", "보기3", "보기4", "정답", "해설"],
                rows=_to_xlsx_rows(questions),
                sheet_name="퀴즈",
            )
            files.append(xlsx_path)
        except Exception as e:
            print(f"[quiz] xlsx 생성 실패: {e}", flush=True)

    return ArtifactResult(
        key=META.key,
        title=META.title,
        markdown=_to_markdown(questions) or "_(문항 생성 실패)_",
        data={"questions": questions},
        files=files,
    )
