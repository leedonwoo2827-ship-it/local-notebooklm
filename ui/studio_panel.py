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

    for i, result in enumerate(reversed(results)):
        slot_id = f"{notebook_name}_{result['key']}_{result['time']}_{i}"
        with st.expander(f"{result['icon']} {result['title']} · {result['time']}", expanded=(i == 0)):
            # unsafe_allow_html=True: 퀴즈의 <details><summary>정답·해설</summary> 같은
            # 접힘 블록을 raw 태그가 아닌 실제 expander 로 렌더링하기 위해 필요.
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

            # 삭제 — 한 번 누르면 확인 영역, 다시 누르면 실제 삭제.
            _render_delete_controls(result, results, slot_id)


def _render_delete_controls(result: dict, results: list, slot_id: str) -> None:
    """두 단계 삭제 UI: [🗑 삭제] → [⚠️ 정말 삭제 / 취소]."""
    confirm_key = f"del_confirm_{slot_id}"

    if not st.session_state.get(confirm_key):
        if st.button("🗑 삭제", key=f"del_{slot_id}", help="이 산출물을 디스크에서 영구 삭제"):
            st.session_state[confirm_key] = True
            st.rerun()
        return

    st.warning("이 산출물의 모든 파일(.md + 동반 파일)이 디스크에서 영구 삭제됩니다.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⚠️ 정말 삭제", key=f"yes_{slot_id}", type="primary", use_container_width=True):
            _delete_result(result, results)
            st.session_state.pop(confirm_key, None)
            st.rerun()
    with c2:
        if st.button("취소", key=f"no_{slot_id}", use_container_width=True):
            st.session_state.pop(confirm_key, None)
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
