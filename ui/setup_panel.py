"""설정 패널 — 헤더 ⚙️ 아이콘에서 열린다.

다음을 한 화면에서 다룬다:
1) LiteLLM 프록시 URL / API 키
2) 모델 프리셋 (저렴/균형/프리미엄) 일괄 적용
3) 프로파일별 개별 모델 선택 (Advanced)
4) PPTX 회사 양식 경로 (선택)

저장 시 `.env` 에 upsert 하고 `core.settings.SETTINGS` 를 즉시 재로드한다.
"""
from __future__ import annotations

import streamlit as st

from core import settings as settings_module
from core.env_writer import update_env


# ── 모델 카탈로그 (docs/pricing.md 와 동기화) ──────────────────────────
# 형식: model_id -> (한 줄 설명, MODEL_EXTRACT 가능 여부)
MODEL_CATALOG: dict[str, tuple[str, bool]] = {
    # DeepSeek
    "deepseek-v4-flash":       ("$0.20/$1.00 · 1M · 저렴 + 한국어 OK",                 False),
    "deepseek-v4-flash-think": ("$0.20/$1.00 · 1M · 추론 사고과정 표시",                False),
    "deepseek-v4-pro":         ("$0.70/$2.80 · 1M · DeepSeek 강화",                    False),
    # Gemini
    "gemini-3.1-flash-lite":   ("$0.05/$0.30 · 1M · 카탈로그 최저가, 한국어 약함",       True),
    "gemini-3-flash-preview":  ("$0.30/$2.50 · 1M · Google 빠른 응답",                  True),
    "gemini-3.1-pro-preview":  ("$1.25/$10.00 · 2M · Google 최상",                      True),
    # OpenAI
    "gpt-5.4-nano":            ("$0.05/$0.40 · OpenAI 미니",                            True),
    "gpt-5.4-mini":            ("$0.25/$2.00 · OpenAI 소형, 인덱싱 권장",               True),
    "gpt-5.5":                 ("$1.25/$10.00 · OpenAI 표준",                           True),
    "gpt-5.5-pro":             ("$5.00/$40.00 · OpenAI 최상",                           True),
    # Claude
    "claude-haiku-4-5":        ("$1.00/$5.00 · 200K · Claude 빠름",                     True),
    "claude-sonnet-4-6":       ("$3.00/$15.00 · 1M · Claude 한국어 강세 (Studio 권장)", True),
    "claude-opus-4-7":         ("$15.00/$75.00 · 1M · Claude 최상",                     True),
}

# 프리셋 — 한 번 클릭으로 4개 프로파일 일괄 적용
PRESETS: dict[str, dict[str, str]] = {
    "⚡ 저렴": {
        "MODEL_CHAT":     "deepseek-v4-flash",
        "MODEL_EXTRACT":  "gpt-5.4-mini",        # DeepSeek json_schema 미지원 우회
        "MODEL_STRONG":   "deepseek-v4-flash",
        "MODEL_CREATIVE": "deepseek-v4-flash",
    },
    "⚖️ 균형": {
        "MODEL_CHAT":     "deepseek-v4-flash",
        "MODEL_EXTRACT":  "gpt-5.4-mini",
        "MODEL_STRONG":   "claude-sonnet-4-6",
        "MODEL_CREATIVE": "claude-sonnet-4-6",
    },
    "💎 프리미엄": {
        "MODEL_CHAT":     "claude-sonnet-4-6",
        "MODEL_EXTRACT":  "claude-sonnet-4-6",
        "MODEL_STRONG":   "claude-opus-4-7",
        "MODEL_CREATIVE": "claude-sonnet-4-6",
    },
}


def render() -> None:
    """설정 박스 본문(헤더의 토글 버튼이 호출)."""
    s = settings_module.SETTINGS

    st.markdown("#### 🔧 설정")
    st.caption(
        "회사에서 발급받은 정보를 입력하세요. 이 PC의 `.env` 에만 저장되며 외부로 전송되지 않습니다."
    )

    # ── 현재 적용 중인 설정 요약 ─────────────────────────────────────
    _render_current_summary(s)

    st.markdown("**🎛 모델 프리셋** — 한 번에 4개 프로파일 일괄 적용")
    pcols = st.columns(len(PRESETS))
    for i, (label, mapping) in enumerate(PRESETS.items()):
        with pcols[i]:
            help_txt = "  ·  ".join(f"{k.removeprefix('MODEL_')}={v}" for k, v in mapping.items())
            if st.button(label, key=f"preset_{i}", use_container_width=True, help=help_txt):
                update_env(mapping)
                settings_module.SETTINGS = settings_module.load()
                st.success(f"{label} 프리셋 적용 완료")
                st.rerun()

    st.divider()

    # ── 메인 폼 (URL/키 + 개별 모델 + 양식 경로) ──────────────────────
    with st.form("api_setup", clear_on_submit=False, border=False):
        st.markdown("**📡 LiteLLM 연결**")
        url = st.text_input(
            "프록시 URL",
            value=s.litellm_url,
            placeholder="http://your-litellm-proxy:4000",
        )
        key = st.text_input(
            "API 키",
            value="",
            placeholder=_mask(s.litellm_key) or "sk-...",
            type="password",
            help="비워두면 기존 키 유지",
        )

        st.markdown("**⚙️ 개별 모델** (고급 — 위 프리셋이면 충분합니다)")

        all_models = list(MODEL_CATALOG.keys())
        extract_models = [m for m, (_, ok) in MODEL_CATALOG.items() if ok]

        mcols = st.columns(2)
        with mcols[0]:
            model_chat = _model_select(
                "채팅 (MODEL_CHAT)", s.model_chat, all_models,
                help_txt="채팅 응답 생성. JSON schema 불필요.",
            )
            model_strong = _model_select(
                "보고서·심층 (MODEL_STRONG)", s.model_strong, all_models,
                help_txt="보고서·마인드맵·플래시카드·퀴즈.",
            )
        with mcols[1]:
            model_extract = _model_select(
                "인덱싱 (MODEL_EXTRACT) ⚠", s.model_extract, extract_models,
                help_txt="LightRAG entity 추출. JSON schema 필요 → DeepSeek 자동 제외됨.",
            )
            model_creative = _model_select(
                "Studio·창작 (MODEL_CREATIVE)", s.model_creative, all_models,
                help_txt="슬라이드·카드뉴스 등 Studio 산출물.",
            )

        st.markdown("**🎨 회사 양식**")
        pptx_template = st.text_input(
            "PPTX 양식 파일 경로 (선택)",
            value=_env_or("PPTX_TEMPLATE_PATH", ""),
            placeholder="assets/pptx_template.pptx (없으면 내장 테마)",
            help="docs/pptx_template_spec.md 참고",
        )

        st.caption("ℹ️ 모델 가격 / 권장 조합: [docs/pricing.md](docs/pricing.md)")

        cols = st.columns([1, 1])
        with cols[0]:
            submitted = st.form_submit_button("저장", use_container_width=True, type="primary")
        with cols[1]:
            closed = st.form_submit_button("닫기", use_container_width=True)

    if closed:
        st.session_state["show_settings"] = False
        st.rerun()

    if not submitted:
        return

    url_clean = url.strip().rstrip("/")
    key_clean = key.strip() or s.litellm_key  # 빈칸이면 기존 키 유지

    if not url_clean or not key_clean:
        st.error("프록시 URL과 API 키를 모두 입력해주세요.")
        return

    update_env({
        "UBION_LITELLM_URL": url_clean,
        "UBION_LITELLM_KEY": key_clean,
        "MODEL_CHAT":        model_chat,
        "MODEL_EXTRACT":     model_extract,
        "MODEL_STRONG":      model_strong,
        "MODEL_CREATIVE":    model_creative,
        "PPTX_TEMPLATE_PATH": pptx_template.strip(),
    })
    settings_module.SETTINGS = settings_module.load()
    st.session_state["show_settings"] = False
    st.success("저장 완료 — 다음 LLM 호출부터 새 설정이 적용됩니다.")
    st.rerun()


def is_configured() -> bool:
    s = settings_module.SETTINGS
    if s.llm_backend == "ollama":
        return True
    return bool(s.litellm_url and s.litellm_key)


# ── 헬퍼 ─────────────────────────────────────────────────────────────
def _render_current_summary(s) -> None:
    """현재 .env 에 저장되어 적용 중인 값을 한눈에 보여준다."""
    url_display = s.litellm_url or "_(미설정)_"
    key_display = _mask(s.litellm_key) or "_(미설정)_"
    template_path = _env_or("PPTX_TEMPLATE_PATH", "") or "_(없음 — 내장 테마 사용)_"

    # 프리셋 매칭 — 현재 모델 조합이 프리셋 중 하나면 라벨로 표시
    current_mapping = {
        "MODEL_CHAT": s.model_chat,
        "MODEL_EXTRACT": s.model_extract,
        "MODEL_STRONG": s.model_strong,
        "MODEL_CREATIVE": s.model_creative,
    }
    preset_label = "사용자 지정"
    for name, mapping in PRESETS.items():
        if mapping == current_mapping:
            preset_label = name
            break

    with st.container(border=True):
        st.markdown(
            f"""
**📋 현재 적용 중**

- **프록시 URL**: `{url_display}`
- **API 키**: `{key_display}`
- **모델 프리셋**: {preset_label}
  - 채팅: `{s.model_chat}`
  - 인덱싱: `{s.model_extract}`
  - 보고서: `{s.model_strong}`
  - Studio: `{s.model_creative}`
- **PPTX 양식**: `{template_path}`
"""
        )


def _model_select(label: str, current: str, choices: list[str], *, help_txt: str = "") -> str:
    """모델 드롭다운. 현재 값이 카탈로그에 없으면 첫 번째로 폴백."""
    try:
        idx = choices.index(current)
    except ValueError:
        idx = 0
    selected = st.selectbox(
        label,
        choices,
        index=idx,
        help=help_txt,
        format_func=lambda m: f"{m}  —  {MODEL_CATALOG.get(m, ('?', True))[0]}",
    )
    return selected


def _env_or(key: str, default: str) -> str:
    import os
    return os.environ.get(key, default)


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "•" * len(value)
    return value[:3] + "•" * 8 + value[-3:]
