"""플래시카드 산출물 — Q/A JSON + Anki .apkg 옵션."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from lightrag.base import QueryParam

from ._base import ArtifactMeta, ArtifactResult, load_prompt

META = ArtifactMeta(
    key="flashcards",
    title="플래시카드",
    icon="🗂️",
    order=40,
    model_profile="strong",
    description="앞면=질문, 뒷면=답 형식의 Q/A 카드 묶음.",
)


def _strip_fence(text: str) -> str:
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    return (m.group(1) if m else text).strip()


def _to_markdown(cards: list[dict]) -> str:
    out = []
    for i, c in enumerate(cards, 1):
        out.append(f"**Q{i}.** {c.get('q', '')}")
        out.append(f"> **A.** {c.get('a', '')}")
        out.append("")
    return "\n".join(out).strip()


def _try_export_anki(cards: list[dict], out_dir: Path, deck_name: str) -> Path | None:
    try:
        import genanki
    except ImportError:
        return None

    deck_id = abs(hash(deck_name)) % (10**9)
    model_id = abs(hash("flashcard-model-v1")) % (10**9)
    model = genanki.Model(
        model_id,
        "LocalNotebookLM Card",
        fields=[{"name": "Q"}, {"name": "A"}],
        templates=[{
            "name": "Card 1",
            "qfmt": "{{Q}}",
            "afmt": "{{FrontSide}}<hr id='answer'>{{A}}",
        }],
    )
    deck = genanki.Deck(deck_id, deck_name)
    for c in cards:
        deck.add_note(genanki.Note(model=model, fields=[c.get("q", ""), c.get("a", "")]))

    out_dir.mkdir(parents=True, exist_ok=True)
    apkg = out_dir / f"flashcards_{int(time.time())}.apkg"
    genanki.Package(deck).write_to_file(str(apkg))
    return apkg


async def generate(rag, context: dict) -> ArtifactResult:
    count = int(context.get("count", 20))
    instruction = load_prompt(META.key) or (
        f"노트북 내용에서 핵심 개념 {count}개를 골라 Q/A 형식 JSON 배열로 출력하라. "
        "각 항목 키: q, a. 최상위는 {\"cards\": [...]}. JSON 외 텍스트 금지."
    )
    raw = await rag.aquery(
        instruction.replace("{{N}}", str(count)),
        param=QueryParam(mode="hybrid", top_k=30),
    )
    try:
        bundle = json.loads(_strip_fence(raw))
        cards = bundle.get("cards") or bundle if isinstance(bundle, list) else bundle.get("cards", [])
    except (json.JSONDecodeError, AttributeError):
        cards = []

    files: list[Path] = []
    artifacts_dir = context.get("artifacts_dir")
    if artifacts_dir and cards:
        apkg = _try_export_anki(cards, Path(artifacts_dir), context.get("deck_name", "노트북"))
        if apkg:
            files.append(apkg)

    return ArtifactResult(
        key=META.key,
        title=META.title,
        markdown=_to_markdown(cards) or "_(카드 생성 실패)_",
        data={"cards": cards},
        files=files,
    )
