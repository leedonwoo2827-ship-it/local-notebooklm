"""Studio artifact contract.

새 산출물을 추가하려면 `studio/<key>.py`에 다음을 구현하라:

    META: ArtifactMeta = ArtifactMeta(
        key="my_artifact", title="내 산출물", icon="✨",
    )

    async def generate(rag, context) -> ArtifactResult: ...
    def render(result) -> None: ...   # Streamlit 표시 (선택, 기본 markdown)

`prompts/<key>_ko.md`를 함께 두면 코드 변경 없이 톤 수정 가능. 앱 재시작 시
`studio/registry.py`가 자동으로 발견해 우측 패널에 버튼을 띄운다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Protocol


@dataclass(frozen=True)
class ArtifactMeta:
    key: str
    title: str
    icon: str = "✨"
    order: int = 100
    model_profile: str = "strong"   # core.llm_client.get_llm_func 와 일치
    accepts: tuple[str, ...] = ("text", "subtitle", "media")
    description: str = ""
    hidden: bool = False  # True 이면 환경변수 STUDIO_VISIBLE 에 명시될 때만 노출


@dataclass
class ArtifactResult:
    key: str
    title: str
    markdown: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    files: list[Path] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def summary(self) -> str:
        return f"{self.title} ({self.created_at:%H:%M})"


GenerateFunc = Callable[..., Awaitable[ArtifactResult]]


class StudioArtifact(Protocol):
    META: ArtifactMeta

    async def generate(self, rag, context: dict) -> ArtifactResult: ...


def load_prompt(key: str) -> str:
    """prompts/<key>_ko.md 를 읽는다. 없으면 빈 문자열."""
    root = Path(__file__).resolve().parent.parent / "prompts"
    candidate = root / f"{key}_ko.md"
    if candidate.exists():
        return candidate.read_text(encoding="utf-8")
    return ""
