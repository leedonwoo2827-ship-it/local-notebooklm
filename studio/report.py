"""HWPX 보고서 산출물 — 노트북 전체 소스를 종합한 .hwpx 보고서."""
from __future__ import annotations

from datetime import datetime

from core.hwpx_export import is_available as hwpx_available, markdown_to_hwpx

from ._base import ArtifactMeta, ArtifactResult, load_prompt

META = ArtifactMeta(
    key="report",
    title="HWPX 보고서",
    icon="📄",
    order=10,
    model_profile="strong",
    description="노트북 전체 소스를 종합한 보고서를 .hwpx 파일로 다운로드.",
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
    answer = answer or "_(빈 응답)_"

    files = []
    notice = ""
    artifacts_dir = context.get("artifacts_dir")
    if artifacts_dir is not None:
        out_dir = artifacts_dir / META.key
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if hwpx_available():
            try:
                hwpx_path = markdown_to_hwpx(answer, out_dir / f"{stamp}.hwpx")
                files.append(hwpx_path)
            except Exception as e:
                notice = f"> ⚠️ HWPX 변환 실패: `{e}` — 본문 Markdown 만 표시합니다.\n\n"
        else:
            notice = (
                "> ⚠️ 한컴 한글이 설치되어 있지 않거나 OLE 가 차단된 환경입니다. "
                "한글이 설치된 Windows 환경에서만 .hwpx 다운로드가 활성화됩니다. "
                "본문은 아래 Markdown 으로 확인하실 수 있습니다.\n\n"
            )

    return ArtifactResult(
        key=META.key,
        title=META.title,
        markdown=notice + answer,
        data={"focus": focus},
        files=files,
    )
