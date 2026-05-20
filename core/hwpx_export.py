"""Markdown 본문 → .hwpx (한컴 한글 OLE 자동화).

한컴 한글이 설치된 Windows 환경에서만 동작한다. 미설치/실패 환경에서는
`is_available()` 가 False 를 돌려주므로 호출 측이 .md 로 폴백한다.

양식 적용은 아직 없다 — markdown 텍스트를 plain 본문으로 삽입한다. 디자인팀에서
양식 .hwpx 를 받으면 차후 `template_path` 인자로 받아 양식 위에 본문을 주입하는
방식으로 업그레이드 예정 (docs/hwpx_template_spec.md 참고).

NOTE: 모듈 로드 시점이 아니라 함수 호출 시점에 win32com 을 import 한다.
Streamlit 이 코드를 reload 해도 stale 한 ImportError 결과가 캐시되지 않도록.
"""
from __future__ import annotations

from pathlib import Path


def _try_dispatch():
    """한컴 한글 COM 객체 dispatch 를 시도. 실패 원인을 그대로 raise."""
    import win32com.client  # type: ignore[import-not-found]

    return win32com.client.Dispatch("HWPFrame.HwpObject")


def _co_init():
    """현재 thread 에서 COM 사용을 초기화. Streamlit 워커 thread 안전 호환."""
    import pythoncom  # type: ignore[import-not-found]

    # CoInitialize 는 thread-local 카운트 기반 — 같은 thread 에서 여러 번 불러도 안전.
    # STA(default) 로 init: 한컴 한글 OLE 는 STA 에서 동작.
    pythoncom.CoInitialize()


def _co_uninit():
    try:
        import pythoncom  # type: ignore[import-not-found]
        pythoncom.CoUninitialize()
    except Exception:
        pass


def is_available() -> bool:
    """한컴 한글이 OLE 로 호출 가능한 환경인지 확인.

    실패 시 콘솔에 정확한 원인을 한 번 찍는다 — 32/64bit 불일치, pywin32 미설치,
    한글 COM 미등록 등의 흔한 원인 진단을 위해.
    """
    try:
        _co_init()
    except Exception as e:
        print(f"[hwpx_export] CoInitialize 실패: {type(e).__name__}: {e}", flush=True)
        return False

    try:
        hwp = _try_dispatch()
    except Exception as e:
        print(
            f"[hwpx_export] OLE 사용 불가: {type(e).__name__}: {e}",
            flush=True,
        )
        _co_uninit()
        return False

    try:
        hwp.Quit()
    except Exception:
        pass
    _co_uninit()
    return True


def markdown_to_hwpx(markdown_text: str, out_path: Path) -> Path:
    """Markdown 본문을 .hwpx 파일로 저장하고 그 경로를 돌려준다.

    Raises:
        RuntimeError: pywin32 미설치 또는 한컴 OLE 실패.
    """
    _co_init()
    try:
        hwp = _try_dispatch()
    except Exception as e:
        _co_uninit()
        raise RuntimeError(
            f"한컴 한글 OLE 호출 실패 ({type(e).__name__}: {e}). "
            "콘솔의 [hwpx_export] 라인을 참고해 주세요."
        ) from e

    out_path = out_path.with_suffix(".hwpx")
    try:
        # 보안 모듈 등록 — 자동화 환경에서 파일 경로 확인 다이얼로그를 우회.
        hwp.RegisterModule("FilePathCheckDLL", "AutomationModule")
        try:
            hwp.XHwpWindows.Item(0).Visible = False
        except Exception:
            # Visible 토글 실패해도 본 작업은 진행.
            pass

        hwp.HAction.Run("FileNew")

        pset = hwp.HParameterSet.HInsertText
        hwp.HAction.GetDefault("InsertText", pset.HSet)
        pset.Text = markdown_text.replace("\r\n", "\n").replace("\n", "\r\n")
        hwp.HAction.Execute("InsertText", pset.HSet)

        # HWPX 저장 — 한컴 표준 액션 방식 (FileSaveAs_S).
        # hwp.SaveAs(path, "HWPX") 직접 호출은 3-arg 시그니처(Path/Format/Arg)에서
        # DISP_E_BADPARAMCOUNT(-2147352562) 가 나기 쉬워, 액션 방식이 가장 안전.
        save_set = hwp.HParameterSet.HFileOpenSave
        hwp.HAction.GetDefault("FileSaveAs_S", save_set.HSet)
        save_set.filename = str(out_path.resolve())
        save_set.Format = "HWPX"
        hwp.HAction.Execute("FileSaveAs_S", save_set.HSet)
    except Exception as e:
        raise RuntimeError(f"HWPX 저장 실패: {e}") from e
    finally:
        try:
            hwp.Quit()
        except Exception:
            pass
        _co_uninit()

    return out_path
