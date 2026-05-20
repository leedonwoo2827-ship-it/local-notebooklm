"""슬라이드 교안(텍스트) 산출물 — 외부 도구(NotebookLM/GPT/Gemini Canvas)에 붙여넣기용.

PPTX 보고서(`studio/slides.py`)와 같은 LLM JSON 흐름을 재사용하되:
  - 프롬프트는 `prompts/slide_outline_ko.md` (강의 교안 톤, 20~30장)
  - 출력은 PPTX 가 아닌 slide-by-slide markdown (.md 파일로 다운로드)
  - 디폴트 장수: 20 (강의 1차시 기준)
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from core.ingest.subtitle import parse_subtitle
from core.rag import NotebookPaths

from ._base import ArtifactMeta, ArtifactResult
from .slides import make_slides_lite

META = ArtifactMeta(
    key="slide_outline",
    title="슬라이드 교안 (텍스트)",
    icon="📋",
    order=22,  # PPTX 보고서(20) 와 카드뉴스(25) 사이
    model_profile="creative",
    accepts=("subtitle", "text"),
    description="강의 교안 톤의 슬라이드 텍스트 (20장 디폴트). NotebookLM/GPT/Gemini Canvas 에 붙여넣기용.",
)


def _bundle_to_outline_markdown(bundle: dict) -> str:
    """make_slides_lite 의 JSON bundle → 외부 도구에 붙여넣기 좋은 markdown."""
    lines: list[str] = []
    title = bundle.get("title") or "강의 교안"
    subtitle = bundle.get("subtitle") or ""
    lines.append(f"# {title}")
    if subtitle:
        lines.append(f"_{subtitle}_")
    lines.append("")

    for i, sl in enumerate(bundle.get("slides", []), 1):
        lines.append(f"## 슬라이드 {i}: {sl.get('title', '')}")
        lines.append("")
        for b in sl.get("bullets", []) or []:
            lines.append(f"- {b}")
        notes = (sl.get("speaker_notes") or "").strip()
        if notes:
            lines.append("")
            lines.append(f"> 강사 메모: {notes}")
        keywords = sl.get("keywords") or []
        if keywords:
            lines.append("")
            lines.append("키워드: " + " · ".join(f"`{k}`" for k in keywords))
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines).strip()


async def generate(rag, context: dict) -> ArtifactResult:
    """노트북 자료 → 강의 교안 슬라이드 텍스트."""
    n_slides = int(context.get("slides", 20))

    # 자막 소스가 있으면 그대로 (PPTX 보고서와 동일 우회 패턴), 없으면 RAG 폴백.
    subtitle_text = context.get("subtitle_text") or ""
    if not subtitle_text:
        notebook_name = context.get("notebook_name", "default")
        paths = NotebookPaths.for_notebook(notebook_name)
        subtitle_files = sorted([
            p for p in paths.sources.glob("*")
            if p.suffix.lower() in {".vtt", ".srt"}
        ])
        if subtitle_files:
            subtitle_text = "\n\n".join(
                f"[{p.stem}]\n{parse_subtitle(p)}" for p in subtitle_files
            )
        else:
            subtitle_text = await rag.aquery(
                "자료/대본 내용을 그대로 긴 문장으로 다시 출력하라. 요약 금지.",
                mode="hybrid",
                top_k=30,
            )

    bundle = await make_slides_lite(
        subtitle_text=subtitle_text,
        subtitle_format=context.get("subtitle_format", "plain"),
        metadata=context.get("metadata"),
        slides=n_slides,
        prompt_key=META.key,
    )
    outline_md = _bundle_to_outline_markdown(bundle)

    files: list[Path] = []
    artifacts_dir = context.get("artifacts_dir")
    if artifacts_dir:
        out_dir = Path(artifacts_dir) / META.key
        out_dir.mkdir(parents=True, exist_ok=True)
        deck_name = (context.get("deck_name") or bundle.get("title") or "slide_outline").strip()
        safe = re.sub(r"[^\w\-가-힣]+", "_", deck_name)[:60] or "slide_outline"
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        outline_path = out_dir / f"{safe}_{stamp}.md"
        outline_path.write_text(outline_md, encoding="utf-8")
        files.append(outline_path)

    return ArtifactResult(
        key=META.key,
        title=META.title,
        markdown=outline_md or "_(교안 생성 실패)_",
        data=bundle,
        files=files,
    )
