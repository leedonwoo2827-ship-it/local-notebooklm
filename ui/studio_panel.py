"""우측 Studio 패널 — studio/registry.discover() 결과를 버튼 그리드로 표시.

새 산출물을 추가하려면 studio/<key>.py + prompts/<key>_ko.md 만 떨어뜨리면 된다.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st

from core.async_runtime import run as run_async
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

    # 노트북마다 디스크에 보관된 과거 산출물을 매번 첫 진입 시 복원해 둔다.
    # session_state 만 쓰면 브라우저 새로고침/앱 재시작 후 "(아직 산출물 없음)"
    # 으로 빈 채로 보임 — 디스크에는 그대로 살아있는데도.
    results_key = f"studio_results_{notebook_name}"
    if results_key not in st.session_state:
        st.session_state[results_key] = _load_persisted(notebook_name, artifacts)
    results: list = st.session_state[results_key]

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

    # 헤더 옆 인라인 삭제 버튼의 테두리를 줄여 expander 헤더와 자연스럽게 맞물리게.
    st.markdown(
        """
        <style>
        /* Studio 우측 패널: '생성된 메모' 영역의 narrow 좌측 column 안 버튼은
           expander 헤더 옆에 인라인으로 붙는 삭제 토글이므로 borderless 처리. */
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child
            div[data-testid="stButton"] button {
            border: 1px solid transparent !important;
            background: transparent !important;
            box-shadow: none !important;
            padding: 0.25rem 0.4rem !important;
            min-height: 0 !important;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child
            div[data-testid="stButton"] button:hover {
            background: rgba(0,0,0,0.04) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    for i, result in enumerate(reversed(results)):
        slot_id = f"{notebook_name}_{result['key']}_{result['time']}_{i}"
        # 다운로드 파일이 동반된 산출물은 헤더 시간 옆에 ⬇ 마커 표시.
        has_files = any(Path(f).exists() for f in (result.get("files") or []))
        dl_marker = "  ⬇" if has_files else ""

        # 좌측 narrow column 에 인라인 삭제 토글, 우측에 본 expander.
        col_del, col_main = st.columns([1, 30])
        with col_del:
            _render_delete_button_inline(result, results, slot_id)
        with col_main:
            with st.expander(
                f"{result['icon']} {result['title']} · {result['time']}{dl_marker}",
                expanded=(i == 0),
            ):
                # unsafe_allow_html=True: 퀴즈의 <details><summary> 같은 접힘 블록을
                # raw 태그가 아니라 실제 expander 로 렌더링하기 위해 필요.
                st.markdown(result["markdown"], unsafe_allow_html=True)
                if result.get("files"):
                    for f in result["files"]:
                        if not Path(f).exists():
                            continue
                        st.download_button(
                            f"⬇ {f.name}",
                            data=Path(f).read_bytes(),
                            file_name=f.name,
                            key=f"dl_{slot_id}_{f.name}",
                        )


def _render_delete_button_inline(result: dict, results: list, slot_id: str) -> None:
    """Expander 헤더 옆에 두는 인라인 삭제 버튼 — 두 단계 확인.

    평소엔 🗑, 한 번 누르면 같은 자리가 ⚠️ 로 바뀌고, 다시 누르면 실제 삭제.
    다른 항목의 🗑 을 누르면 자동으로 직전 confirm 은 해제 — 동시에 두 항목이
    confirm 상태가 되지 않도록.
    """
    confirm_key = f"del_confirm_{slot_id}"
    if st.session_state.get(confirm_key):
        if st.button(
            "⚠️",
            key=f"yes_{slot_id}",
            help="다시 누르면 영구 삭제. 다른 항목의 🗑 을 누르면 자동 취소됩니다.",
        ):
            _delete_result(result, results)
            st.session_state.pop(confirm_key, None)
            st.rerun()
    else:
        if st.button("🗑", key=f"del_{slot_id}", help="삭제 (한 번 더 누르면 확정)"):
            for k in list(st.session_state.keys()):
                if k.startswith("del_confirm_") and k != confirm_key:
                    st.session_state.pop(k, None)
            st.session_state[confirm_key] = True
            st.rerun()


def _delete_result(result: dict, results: list) -> None:
    """디스크 파일 + session_state 결과 동시 삭제."""
    md_path = result.get("md_path")
    if md_path and Path(md_path).exists():
        try:
            Path(md_path).unlink()
        except Exception as e:
            print(f"[studio_panel] md 삭제 실패: {e}", flush=True)
    for f in result.get("files") or []:
        try:
            if Path(f).exists():
                Path(f).unlink()
        except Exception as e:
            print(f"[studio_panel] 동반파일 삭제 실패 {f}: {e}", flush=True)
    try:
        results.remove(result)
    except ValueError:
        pass


def _load_persisted(notebook_name: str, artifacts: list[RegisteredArtifact]) -> list:
    """과거 세션에서 만든 산출물을 `data/notebooks/<name>/artifacts/` 에서 복원.

    같은 timestamp(파일 stem) 의 `.md` + 동반 파일(`.hwpx`/`.pptx`/`.png` 등)을
    한 묶음으로 모은다. studio 모듈이 사라졌다면(plugin 제거) 그 디렉터리는 무시.
    """
    paths = NotebookPaths.for_notebook(notebook_name)
    if not paths.artifacts.exists():
        return []

    meta_by_key = {a.meta.key: a.meta for a in artifacts}
    restored: list = []

    for art_dir in paths.artifacts.iterdir():
        if not art_dir.is_dir():
            continue
        meta = meta_by_key.get(art_dir.name)
        if meta is None:
            continue

        # stamp -> {"md": Path | None, "files": [Path, ...]}
        groups: dict[str, dict] = {}
        for f in art_dir.iterdir():
            if not f.is_file():
                continue
            g = groups.setdefault(f.stem, {"md": None, "files": []})
            if f.suffix.lower() == ".md":
                g["md"] = f
            else:
                g["files"].append(f)

        for stamp in sorted(groups):
            g = groups[stamp]
            if g["md"] is None:
                continue
            try:
                md = g["md"].read_text(encoding="utf-8")
            except Exception:
                continue
            try:
                t = datetime.strptime(stamp, "%Y%m%d_%H%M%S").strftime("%m-%d %H:%M")
            except ValueError:
                t = stamp
            restored.append({
                "key": meta.key,
                "title": meta.title,
                "icon": meta.icon,
                "markdown": md,
                "files": sorted(g["files"]),
                "time": t,
                "md_path": g["md"],
            })
    return restored


def _run_artifact(art: RegisteredArtifact, notebook_name: str, results: list) -> bool:
    """Return True on success. 실패 시 콘솔/UI 양쪽에 에러를 남긴다."""
    import traceback

    paths = NotebookPaths.for_notebook(notebook_name)
    context = {
        "notebook_name": notebook_name,
        "artifacts_dir": paths.artifacts,
        "deck_name": notebook_name,
    }

    print(f"\n[Studio] {art.meta.title} 시작 (notebook={notebook_name})", flush=True)

    with st.spinner(f"{art.meta.title} 생성 중..."):
        async def _go():
            rag = await build_rag(notebook_name)
            return await art.generate(rag, context)

        try:
            result = run_async(_go())
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[Studio] {art.meta.title} 실패:\n{tb}", flush=True)
            # st.rerun() 으로 사라지지 않도록 session_state 에 보관
            st.session_state["studio_last_error"] = (
                f"**{art.meta.title} 생성 실패**\n\n```\n{type(e).__name__}: {e}\n```"
            )
            return False

    print(f"[Studio] {art.meta.title} 완료 (files={len(result.files)})", flush=True)

    out_dir = paths.artifacts / result.key
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = out_dir / f"{stamp}.md"
    md_path.write_text(result.markdown, encoding="utf-8")

    results.append({
        "key": result.key,
        "title": result.title,
        "icon": art.meta.icon,
        "markdown": result.markdown,
        "files": result.files,
        "time": datetime.now().strftime("%H:%M:%S"),
        "md_path": md_path,
    })
    return True
