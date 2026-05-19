"""Local NotebookLM — 3-패널 Streamlit 엔트리.

좌(출처) | 중(채팅) | 우(Studio).
키 설정은 헤더 우측의 ⚙️ 아이콘으로 열리는 인라인 패널에서 받는다.
"""
from __future__ import annotations

import streamlit as st

from ui import chat_panel, setup_panel, sources_panel, studio_panel


st.set_page_config(
    page_title="Local NotebookLM",
    page_icon="📓",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
        section.main > div { padding-top: 0.5rem; }
        div[data-testid="stHorizontalBlock"] { align-items: flex-start; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 키가 아직 없으면 첫 진입 시 설정 패널을 자동으로 펼친다 (한 번만)
    if "show_settings" not in st.session_state:
        st.session_state["show_settings"] = not setup_panel.is_configured()

    header_left, header_right = st.columns([8, 1])
    with header_left:
        st.title("📓 Local NotebookLM")
        st.caption("RAG-Anything · LiteLLM 프록시 · 로컬 BGE-M3")
    with header_right:
        st.write("")
        if st.button("⚙️", help="LiteLLM 키 / URL 설정", use_container_width=True):
            st.session_state["show_settings"] = not st.session_state["show_settings"]
            st.rerun()

    if st.session_state["show_settings"]:
        with st.container(border=True):
            setup_panel.render()

    if not setup_panel.is_configured():
        st.warning("우상단 ⚙️ 에서 LiteLLM URL과 키를 먼저 입력하세요. 입력 전에는 LLM 호출이 실패합니다.")

    col_sources, col_chat, col_studio = st.columns([1.1, 2.0, 1.4], gap="medium")

    with col_sources:
        sources_panel.render()
    with col_chat:
        chat_panel.render()
    with col_studio:
        studio_panel.render()


if __name__ == "__main__":
    main()
