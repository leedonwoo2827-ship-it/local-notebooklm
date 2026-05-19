"""우측 Studio 패널 — studio/registry.discover() 결과를 버튼 그리드로 표시.

새 산출물을 추가하려면 studio/<key>.py + prompts/<key>_ko.md 만 떨어뜨리면 된다.
"""
from __future__ import annotations

import asyncio
from datetime import datetime

import streamlit as st

from core.rag import NotebookPaths, build_rag, list_sources
from studio.registry import RegisteredArtifact, discover


def render() -> None:
    notebook_name = st.session_state.get("notebook_name", "default")
    sources = list_sources(notebook_name)

    st.markdown("### 🛠️ Studio")

    if not sources:
        st.info("소스를 먼저 업로드하세요.")
        return

    artifacts = discover()
    if not artifacts:
        st.warning("등록된 산출물이 없습니다. studio/ 폴더에 모듈을 추가하세요.")
        return

    results_key = f"studio_results_{notebook_name}"
    results: list = st.session_state.setdefault(results_key, [])

    cols = st.columns(2)
    for idx, art in enumerate(artifacts):
        with cols[idx % 2]:
            if st.button(
                f"{art.meta.icon} {art.meta.title}",
                key=f"studio_btn_{notebook_name}_{art.meta.key}",
                use_container_width=True,
                help=art.meta.description,
            ):
                _run_artifact(art, notebook_name, results)
                st.rerun()

    st.divider()
    st.caption("생성된 메모")
    if not results:
        st.write("_(아직 산출물 없음)_")
        return

    for i, result in enumerate(reversed(results)):
        with st.expander(f"{result['icon']} {result['title']} · {result['time']}", expanded=(i == 0)):
            st.markdown(result["markdown"])
            if result.get("files"):
                for f in result["files"]:
                    st.download_button(
                        f"⬇ {f.name}",
                        data=f.read_bytes(),
                        file_name=f.name,
                        key=f"dl_{notebook_name}_{result['time']}_{f.name}",
                    )


def _run_artifact(art: RegisteredArtifact, notebook_name: str, results: list) -> None:
    paths = NotebookPaths.for_notebook(notebook_name)
    context = {
        "notebook_name": notebook_name,
        "artifacts_dir": paths.artifacts,
        "deck_name": notebook_name,
    }

    with st.spinner(f"{art.meta.title} 생성 중..."):
        async def _go():
            rag = await build_rag(notebook_name)
            return await art.generate(rag, context)

        try:
            result = asyncio.run(_go())
        except Exception as e:
            st.error(f"{art.meta.title} 생성 실패: {e}")
            return

    results.append({
        "key": result.key,
        "title": result.title,
        "icon": art.meta.icon,
        "markdown": result.markdown,
        "files": result.files,
        "time": datetime.now().strftime("%H:%M:%S"),
    })

    out_dir = paths.artifacts / result.key
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (out_dir / f"{stamp}.md").write_text(result.markdown, encoding="utf-8")
