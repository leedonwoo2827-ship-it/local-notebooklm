"""중앙 Citation 채팅 패널."""
from __future__ import annotations

import asyncio

import streamlit as st

from core.rag import build_rag, list_sources
from studio._base import load_prompt


def render() -> None:
    notebook_name = st.session_state.get("notebook_name", "default")
    sources = list_sources(notebook_name)

    st.markdown(f"### 💬 채팅 — `{notebook_name}` · 소스 {len(sources)}개")

    history_key = f"chat_{notebook_name}"
    history = st.session_state.setdefault(history_key, [])

    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not sources:
        st.info("좌측에서 소스를 업로드하면 질의응답을 시작할 수 있습니다.")
        return

    prompt = st.chat_input("질문하거나 창작하세요")
    if not prompt:
        return

    history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        with st.spinner("답변 생성 중..."):
            answer = asyncio.run(_query(notebook_name, prompt))
        placeholder.markdown(answer)

    history.append({"role": "assistant", "content": answer})


async def _query(notebook_name: str, prompt: str) -> str:
    rag = await build_rag(notebook_name)
    system = load_prompt("citation_qa") or ""
    full_prompt = f"{system}\n\n[질문]\n{prompt}" if system else prompt
    return await rag.aquery(
        full_prompt,
        mode="hybrid",
        top_k=20,
        response_type="Markdown with citations",
    )
