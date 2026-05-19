"""설정 — 프록시 URL + API 키 2칸. 헤더 ⚙️ 아이콘에서 열린다."""
from __future__ import annotations

import streamlit as st

from core import settings as settings_module
from core.env_writer import update_env


def render() -> None:
    """설정 박스 본문(헤더의 토글 버튼이 호출)."""
    st.markdown("#### 🔧 LiteLLM 프록시 설정")
    st.caption("회사에서 발급받은 정보를 입력하세요. 이 PC의 `.env`에만 저장됩니다.")

    with st.form("api_setup", clear_on_submit=False, border=False):
        url = st.text_input(
            "프록시 URL",
            value=settings_module.SETTINGS.litellm_url,
            placeholder="http://your-litellm-proxy:4000",
        )
        key = st.text_input(
            "API 키",
            value="",
            placeholder=_mask(settings_module.SETTINGS.litellm_key) or "sk-...",
            type="password",
        )
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
    key_clean = key.strip() or settings_module.SETTINGS.litellm_key  # 빈칸이면 기존 키 유지

    if not url_clean or not key_clean:
        st.error("URL과 키를 모두 입력해주세요.")
        return

    update_env({
        "UBION_LITELLM_URL": url_clean,
        "UBION_LITELLM_KEY": key_clean,
    })
    settings_module.SETTINGS = settings_module.load()
    st.session_state["show_settings"] = False
    st.success("저장 완료.")
    st.rerun()


def is_configured() -> bool:
    s = settings_module.SETTINGS
    if s.llm_backend == "ollama":
        return True
    return bool(s.litellm_url and s.litellm_key)


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "•" * len(value)
    return value[:3] + "•" * 8 + value[-3:]
