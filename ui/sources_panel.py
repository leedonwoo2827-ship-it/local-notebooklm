"""좌측 출처(Sources) 패널 — 파일 업로드 + 소스 목록 + 노트북 선택/생성."""
from __future__ import annotations

import asyncio
from pathlib import Path

import streamlit as st

from core.ingest.hwpx import hwpx_to_pdf
from core.ingest.media import is_media, media_to_text
from core.rag import NotebookPaths, build_rag, list_notebooks, list_sources

SUPPORTED_EXTENSIONS = [
    "pdf", "docx", "txt", "md", "hwpx",
    "srt", "vtt",
    "mp4", "m4a", "mp3", "wav", "webm", "mov",
]


def render() -> None:
    st.markdown("### 📚 출처")

    notebooks = list_notebooks() or ["default"]
    selected = st.session_state.get("notebook_name") or notebooks[0]
    if selected not in notebooks:
        notebooks.append(selected)

    chosen = st.selectbox("노트북", notebooks, index=notebooks.index(selected))
    new_name = st.text_input("새 노트북 만들기", "", placeholder="예: dissertation")
    if st.button("＋ 노트북 생성", use_container_width=True) and new_name.strip():
        st.session_state["notebook_name"] = new_name.strip()
        NotebookPaths.for_notebook(new_name.strip()).ensure()
        st.rerun()

    st.session_state["notebook_name"] = chosen
    paths = NotebookPaths.for_notebook(chosen)
    paths.ensure()

    st.divider()

    uploaded = st.file_uploader(
        "＋ 소스 추가",
        type=SUPPORTED_EXTENSIONS,
        accept_multiple_files=True,
        key=f"uploader_{chosen}",
    )
    if uploaded:
        _ingest_uploads(uploaded, paths)

    st.divider()
    st.caption("등록된 소스")
    sources = list_sources(chosen)
    if not sources:
        st.info("아직 업로드된 소스가 없습니다.")
        return

    selected_keys = []
    for src in sources:
        key = f"src_{chosen}_{src.name}"
        checked = st.checkbox(src.name, value=True, key=key)
        if checked:
            selected_keys.append(src)
    st.session_state["selected_sources"] = selected_keys


def _ingest_uploads(files, paths: NotebookPaths) -> None:
    progress = st.empty()
    for f in files:
        target = paths.sources / f.name
        target.write_bytes(f.read())
        progress.write(f"저장: {f.name}")

        try:
            asyncio.run(_post_process(target, paths))
        except Exception as e:
            st.error(f"{f.name} 처리 실패: {e}")
            continue

    progress.success(f"{len(files)}개 소스 처리 완료. 인덱싱은 채팅 시작 시 진행됩니다.")


async def _post_process(target: Path, paths: NotebookPaths) -> None:
    """업로드 후 즉시 RAG 인입까지 끝낸다.

    텍스트 계열(VTT/SRT/TXT/MD/STT 결과)은 MinerU 비전 모델을 우회하고
    `insert_content_list`로 직접 인입한다 — CPU PC에서 page당 54초가
    page당 1-2초로 떨어진다. PDF/Docx/HWPX(변환후)만 MinerU 거침.
    """
    rag = await build_rag(paths.name)

    if target.suffix.lower() == ".hwpx":
        target = hwpx_to_pdf(target, paths.sources)

    if is_media(target):
        target = await media_to_text(target, paths.sources)

    if target.suffix.lower() in {".srt", ".vtt"}:
        from core.ingest.subtitle import parse_subtitle
        text = parse_subtitle(target)
        await rag.insert_content_list(
            [{"type": "text", "text": text, "page_idx": 0}],
            file_path=target.name,
        )
        return

    if target.suffix.lower() in {".txt", ".md"}:
        text = target.read_text(encoding="utf-8", errors="ignore")
        await rag.insert_content_list(
            [{"type": "text", "text": text, "page_idx": 0}],
            file_path=target.name,
        )
        return

    await rag.process_document_complete(file_path=str(target))
