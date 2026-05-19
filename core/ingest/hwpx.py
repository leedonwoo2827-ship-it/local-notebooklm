"""HWPX → PDF 변환 어댑터.

RAG-Anything이 HWPX를 native로 지원하지 않으므로 LibreOffice headless로
PDF로 변환한 뒤 MinerU 파서로 인입한다.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class HwpxConversionError(RuntimeError):
    pass


def _find_soffice() -> str:
    for name in ("soffice", "libreoffice"):
        path = shutil.which(name)
        if path:
            return path
    # Windows 기본 설치 경로
    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    raise HwpxConversionError(
        "LibreOffice를 찾을 수 없습니다. https://www.libreoffice.org/download/ 에서 설치 후 PATH 등록 필요."
    )


def hwpx_to_pdf(hwpx_path: Path, out_dir: Path) -> Path:
    """Return the converted PDF path. Idempotent: skips if PDF already newer."""
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / (hwpx_path.stem + ".pdf")

    if pdf_path.exists() and pdf_path.stat().st_mtime >= hwpx_path.stat().st_mtime:
        return pdf_path

    soffice = _find_soffice()
    result = subprocess.run(
        [
            soffice,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(out_dir),
            str(hwpx_path),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0 or not pdf_path.exists():
        raise HwpxConversionError(
            f"LibreOffice 변환 실패 (rc={result.returncode}): {result.stderr[:500]}"
        )
    return pdf_path
