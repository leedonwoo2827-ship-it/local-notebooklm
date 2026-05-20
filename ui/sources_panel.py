"""좌측 출처(Sources) 패널 — 파일 업로드 + 소스 목록 + 노트북 선택/생성."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.async_runtime import run as run_async
from core.ingest.hwpx import hwpx_to_pdf
from core.ingest.media import is_media, media_to_text
from core.ingest.text_extract import docx_to_text, pdf_to_text
from core.rag import NotebookPaths, ainsert_text, build_rag, list_notebooks, list_sources
from core.settings import SETTINGS

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
    # Streamlit 은 위젯 값이 재실행 사이에도 살아있어서, 같은 file_uploader 결과로
    # _ingest_uploads 가 매 rerun 마다 호출된다. 같은 파일을 두 번 enqueue 하면
    # LightRAG 가 첫 번째 처리(HANDLING)와 두 번째 호출을 충돌시켜 duplicate 로
    # 분류 → chunks_count=0 인 빈 doc 만 남음. session_state 로 1회 처리 가드.
    if uploaded:
        processed_key = f"ingested_{chosen}"
        already = st.session_state.setdefault(processed_key, set())
        fresh = [f for f in uploaded if (f.name, getattr(f, "size", None)) not in already]
        if fresh:
            _ingest_uploads(fresh, paths)
            for f in fresh:
                already.add((f.name, getattr(f, "size", None)))

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
            run_async(_post_process(target, paths))
        except Exception as e:
            st.error(f"{f.name} 처리 실패: {e}")
            continue

    progress.success(f"{len(files)}개 소스 처리 완료.")


async def _post_process(target: Path, paths: NotebookPaths) -> None:
    """업로드 후 즉시 RAG 인입까지 끝낸다.

    본 앱은 OCR/멀티모달 분기를 의도적으로 끄고 LightRAG 의 텍스트 KG 파이프라인만
    사용한다. 따라서 입력은 모두 텍스트 추출이 가능한 형식이어야 한다:
      · 자막 (srt/vtt) / 평문 (txt/md)
      · PDF (텍스트 추출 가능본 — pypdf)
      · Docx (python-docx)
      · HWPX → PDF 변환 후 텍스트 추출
      · MP4/m4a/mp3/wav/webm/mov → Whisper STT 후 텍스트

    스캔/이미지 PDF 는 미지원. (외부 OCR 로 .txt 만들어 다시 올리도록 안내)
    """
    rag = await build_rag(paths.name)

    if target.suffix.lower() == ".hwpx":
        target = hwpx_to_pdf(target, paths.sources)

    if is_media(target):
        target = await media_to_text(target, paths.sources)

    ext = target.suffix.lower()
    if ext in {".srt", ".vtt"}:
        from core.ingest.subtitle import parse_subtitle
        text = parse_subtitle(target)
    elif ext in {".txt", ".md"}:
        text = target.read_text(encoding="utf-8", errors="ignore")
    elif ext == ".pdf":
        if SETTINGS.enable_mineru:
            await rag.process_document_complete(file_path=str(target))
            return
        text = pdf_to_text(target)
        if not text.strip():
            raise RuntimeError(
                "PDF 에서 텍스트를 추출하지 못했습니다 (스캔/이미지 PDF 로 추정). "
                "외부 OCR 로 .txt 를 만들어 다시 업로드해 주세요."
            )
    elif ext == ".docx":
        text = docx_to_text(target)
    else:
        raise RuntimeError(f"지원하지 않는 형식: {ext}")

    await ainsert_text(rag, text, target.name)
