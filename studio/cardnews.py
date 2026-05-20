"""카드뉴스(인포그래픽) 산출물.

자막 텍스트 → LLM JSON → Jinja2 HTML 템플릿 → Playwright PNG 캡처.
회차별 1장씩 + 전체 통합 1장 = N+1 장 생성.

lecture-postpro-mcp 의 make_cardnews() 가 이 모듈의 순수 async 함수
(`make_cardnews_lite`, `render_card_html`, `capture_png`)를 그대로 import해서
사용한다. Streamlit/RAG 의존은 generate() 안에만 둔다.
"""
from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable, Literal

from core.llm_client import get_llm_func
from core.ingest.subtitle import parse_subtitle, parse_subtitle_text
from core.rag import NotebookPaths

from ._base import ArtifactMeta, ArtifactResult, load_prompt

META = ArtifactMeta(
    key="cardnews",
    title="카드뉴스",
    icon="🖼️",
    order=25,
    model_profile="creative",
    accepts=("subtitle", "text"),
    description="자막을 인포그래픽 카드뉴스(HTML + PNG)로. 회차별 + 종합.",
)


LLMFunc = Callable[..., Awaitable[str]]

CARD_WIDTH = 1080
CARD_HEIGHT = 1620


# ── HTML 템플릿 (Jinja2) ─────────────────────────────────────────────
HTML_TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<title>{{ headline }}</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    width: {{ width }}px;
    font-family: 'Pretendard', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
    background: #f6f8fc;
    color: #181b2c;
  }
  .card {
    width: {{ width }}px;
    padding: 56px 56px 56px;
    background: linear-gradient(180deg, #f6f8fc 0%, #eef2f8 100%);
  }
  .hero {
    display: flex;
    gap: 24px;
    align-items: center;
    padding-bottom: 28px;
    border-bottom: 2px solid #1f2a44;
    margin-bottom: 36px;
  }
  .hero .emoji { font-size: 88px; line-height: 1; }
  .hero .headline {
    font-size: 60px;
    font-weight: 800;
    line-height: 1.15;
    color: #1f2a44;
    margin: 0 0 10px;
    letter-spacing: -1px;
  }
  .hero .subhead {
    font-size: 26px;
    color: #2e5bff;
    font-weight: 600;
    margin: 0;
    line-height: 1.4;
  }
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 22px;
    margin-bottom: 36px;
  }
  .sec {
    background: #ffffff;
    border-radius: 18px;
    padding: 24px 26px;
    box-shadow: 0 6px 18px rgba(31, 42, 68, 0.06);
    position: relative;
    min-height: 220px;
  }
  .sec .num {
    position: absolute;
    top: 18px; right: 22px;
    font-size: 14px;
    color: #2e5bff;
    font-weight: 800;
    letter-spacing: 1px;
  }
  .sec .icon { font-size: 38px; line-height: 1; margin-bottom: 10px; }
  .sec .title {
    font-size: 24px;
    font-weight: 800;
    color: #181b2c;
    margin: 0 0 10px;
    letter-spacing: -0.5px;
  }
  .sec .body {
    font-size: 17px;
    color: #41475a;
    line-height: 1.55;
    margin: 0 0 12px;
  }
  .sec .tags { display: flex; gap: 8px; flex-wrap: wrap; }
  .sec .tag {
    font-size: 12px;
    color: #2e5bff;
    background: #e7eeff;
    padding: 4px 10px;
    border-radius: 999px;
    font-weight: 600;
  }
  .summary {
    background: #1f2a44;
    color: #fff;
    border-radius: 18px;
    padding: 24px 28px;
  }
  .summary .label {
    font-size: 18px;
    font-weight: 700;
    margin: 0 0 16px;
    letter-spacing: 0.3px;
  }
  .summary .row { display: flex; justify-content: space-between; gap: 14px; }
  .summary .pill {
    flex: 1;
    background: rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 14px 10px;
    text-align: center;
  }
  .summary .pill .ic { font-size: 28px; display: block; margin-bottom: 6px; }
  .summary .pill .tx { font-size: 13px; color: #d6def4; line-height: 1.3; }
</style>
</head>
<body>
  <div class="card">
    <div class="hero">
      <div class="emoji">{{ hero_icon }}</div>
      <div>
        <h1 class="headline">{{ headline }}</h1>
        <p class="subhead">{{ subhead }}</p>
      </div>
    </div>

    <div class="grid">
      {% for s in sections %}
      <div class="sec">
        <span class="num">{{ "%02d"|format(loop.index) }}</span>
        <div class="icon">{{ s.icon }}</div>
        <h2 class="title">{{ s.title }}</h2>
        <p class="body">{{ s.body }}</p>
        <div class="tags">
          {% for t in s.tags or [] %}<span class="tag">#{{ t }}</span>{% endfor %}
        </div>
      </div>
      {% endfor %}
    </div>

    {% if summary_bar %}
    <div class="summary">
      <p class="label">{{ summary_bar.label }}</p>
      <div class="row">
        {% for it in summary_bar.pills %}
        <div class="pill">
          <span class="ic">{{ it.icon }}</span>
          <span class="tx">{{ it.text }}</span>
        </div>
        {% endfor %}
      </div>
    </div>
    {% endif %}
  </div>
</body>
</html>
"""


def _strip_fence(text: str) -> str:
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    return (m.group(1) if m else text).strip()


def _to_markdown_preview(card: dict, image_paths: list[Path]) -> str:
    """Studio 패널 미리보기용 마크다운."""
    lines: list[str] = []
    if card.get("headline"):
        lines.append(f"# {card['hero_icon']} {card['headline']}")
    if card.get("subhead"):
        lines.append(f"_{card['subhead']}_")
        lines.append("")
    for i, s in enumerate(card.get("sections", []), 1):
        lines.append(f"**{i:02d}. {s.get('icon','')} {s.get('title','')}** — {s.get('body','')}")
    sb = card.get("summary_bar") or {}
    pills = sb.get("pills") or sb.get("items") or []  # 구버전 응답 호환
    if pills:
        lines.append("")
        lines.append("**" + sb.get("label", "한눈에") + "**: " +
                     "  ·  ".join(f"{it.get('icon','')} {it.get('text','')}" for it in pills))
    if image_paths:
        lines.append("")
        lines.append("📸 캡처 이미지: " + ", ".join(f"`{p.name}`" for p in image_paths))
    return "\n".join(lines).strip()


# ── 순수 async API (MCP 재사용) ─────────────────────────────────────
async def make_cardnews_lite(
    subtitle_text: str,
    subtitle_format: Literal["srt", "vtt", "plain"] = "plain",
    metadata: dict | None = None,
    llm_call: LLMFunc | None = None,
) -> dict:
    """자막 텍스트 → 카드뉴스 콘텐츠 JSON. RAG/Streamlit 비의존."""
    clean = (
        parse_subtitle_text(subtitle_text, subtitle_format)
        if subtitle_format in ("srt", "vtt")
        else subtitle_text
    )

    prompt_tpl = load_prompt("cardnews") or (
        "다음 텍스트로부터 카드뉴스용 JSON을 만들어라."
    )
    prompt = (
        prompt_tpl
        + "\n\n[메타데이터]\n"
        + json.dumps(metadata or {}, ensure_ascii=False)
        + "\n\n[자막]\n"
        + clean
    )

    caller = llm_call or get_llm_func("creative")
    raw = await caller(prompt)
    payload = _strip_fence(raw)
    try:
        card = json.loads(payload)
    except json.JSONDecodeError:
        card = {
            "headline": "파싱 실패",
            "subhead": "LLM 응답을 JSON으로 해석하지 못함",
            "hero_icon": "⚠️",
            "sections": [{"icon": "📄", "title": "원본", "body": raw[:120], "tags": []}],
            "summary_bar": None,
            "footer": "",
        }

    card.setdefault("headline", "카드뉴스")
    card.setdefault("subhead", "")
    card.setdefault("hero_icon", "📌")
    card.setdefault("sections", [])
    card.setdefault("footer", "")
    return card


def render_card_html(card: dict, width: int = CARD_WIDTH, height: int = CARD_HEIGHT) -> str:
    """카드 JSON → HTML 문자열. Jinja2 사용."""
    from jinja2 import Template
    tpl = Template(HTML_TEMPLATE)
    return tpl.render(width=width, height=height, **card)


async def capture_png(html: str, png_path: Path, width: int = CARD_WIDTH, height: int = CARD_HEIGHT) -> Path:
    """HTML 문자열 → PNG 캡처. Playwright 사용. 동기 호출이 필요할 경우 asyncio.run."""
    from playwright.async_api import async_playwright

    png_path.parent.mkdir(parents=True, exist_ok=True)
    html_path = png_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={"width": width, "height": height},
                                        device_scale_factor=2)
        page = await ctx.new_page()
        await page.goto(html_path.as_uri())
        # 폰트 로드 대기
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=str(png_path), full_page=True)
        await browser.close()

    return png_path


# ── 회차별 + 종합 작업 묶음 ─────────────────────────────────────────
async def _build_one(
    label: str,
    subtitle_text: str,
    subtitle_format: Literal["srt", "vtt", "plain"],
    out_dir: Path,
    stamp: str,
    metadata: dict | None = None,
) -> tuple[Path, Path, dict]:
    """단일 카드뉴스: JSON → HTML → PNG. (html_path, png_path, card_dict) 반환."""
    card = await make_cardnews_lite(
        subtitle_text=subtitle_text,
        subtitle_format=subtitle_format,
        metadata=metadata,
    )
    safe_label = re.sub(r"[^\w\-가-힣]+", "_", label)[:60] or "card"
    base = out_dir / f"{stamp}_{safe_label}"
    html = render_card_html(card)
    png_path = await capture_png(html, base.with_suffix(".png"))
    html_path = base.with_suffix(".html")  # capture_png 에서 이미 저장됨
    return html_path, png_path, card


# ── Studio entrypoint ────────────────────────────────────────────────
async def generate(rag, context: dict) -> ArtifactResult:
    """노트북의 자막 소스마다 카드뉴스 1장 + 전체 통합본 1장."""
    notebook_name = context.get("notebook_name", "default")
    paths = NotebookPaths.for_notebook(notebook_name)
    artifacts_dir = Path(context.get("artifacts_dir") or paths.artifacts)
    out_dir = artifacts_dir / META.key
    out_dir.mkdir(parents=True, exist_ok=True)

    # 자막 소스 직접 읽기 (RAG 의존 없음 — 인덱싱 미완성이어도 OK)
    subtitle_files = sorted([
        p for p in paths.sources.glob("*")
        if p.suffix.lower() in {".vtt", ".srt"}
    ])

    if not subtitle_files:
        # 자막이 없으면 RAG에 폴백 — 노트북 전체 텍스트로 한 장만
        try:
            text = await rag.aquery(
                "자막/대본 내용을 그대로 긴 문장으로 다시 출력하라. 요약 금지.",
                mode="hybrid",
                top_k=20,
            )
        except Exception:
            text = ""
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _, png, card = await _build_one("종합", text or "", "plain", out_dir, stamp)
        return ArtifactResult(
            key=META.key, title=META.title,
            markdown=_to_markdown_preview(card, [png]),
            data={"cards": [card]},
            files=[png],
        )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cards: list[dict] = []
    pngs: list[Path] = []

    # 회차별
    combined_chunks: list[str] = []
    for vtt_path in subtitle_files:
        fmt: Literal["srt", "vtt"] = "vtt" if vtt_path.suffix.lower() == ".vtt" else "srt"
        text = parse_subtitle(vtt_path)
        combined_chunks.append(f"[{vtt_path.stem}]\n{text}")
        _, png, card = await _build_one(
            vtt_path.stem, text, "plain", out_dir, stamp,
            metadata={"source": vtt_path.name},
        )
        pngs.append(png)
        cards.append(card)

    # 종합 — 전체 자막 합쳐 한 장
    if len(subtitle_files) > 1:
        merged = "\n\n".join(combined_chunks)
        _, png, card = await _build_one(
            "종합", merged, "plain", out_dir, stamp,
            metadata={"source": "all_episodes_merged"},
        )
        pngs.append(png)
        cards.append(card)

    last_card = cards[-1] if cards else {}
    return ArtifactResult(
        key=META.key, title=META.title,
        markdown=_to_markdown_preview(last_card, pngs),
        data={"cards": cards},
        files=pngs,
    )


def render(result: ArtifactResult) -> None:
    """Streamlit 표시 — 생성된 PNG들을 순서대로 표시 + 다운로드 버튼."""
    import streamlit as st

    if result.files:
        st.success(f"카드뉴스 {len(result.files)}장 생성 완료")
        for png in result.files:
            st.image(str(png), caption=png.name, use_container_width=True)
    st.markdown(result.markdown or "_(빈 결과)_")
