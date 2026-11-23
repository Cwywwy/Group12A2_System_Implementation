# -*- coding: utf-8 -*-
"""
pdf_export.py
Author: Group12A2 DSW Team
Purpose: Export a .docx deliverable to .pdf through Word automation and verify
         the produced file, without depending on an optional pywin32 install.
Module: src.reporting

Revision History
----------------
2026-11-24  initial version: COM export over python or PowerShell, page-count
            verification with pypdf.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

__all__ = ["count_pdf_pages", "export_pdf"]


def count_pdf_pages(path: str | Path) -> int:
    """Return the page count of a PDF, or zero when it cannot be read."""
    try:
        from pypdf import PdfReader
    except ImportError:  # pragma: no cover - pypdf is a project dependency
        return 0
    try:
        return len(PdfReader(str(path)).pages)
    except Exception:  # noqa: BLE001 - a corrupt file reports zero pages
        return 0


def _export_with_python(source: Path, target: Path) -> None:
    """Export through pywin32 when it is installed."""
    import win32com.client  # type: ignore  # noqa: F401

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        document = word.Documents.Open(str(source))
        try:
            document.SaveAs(str(target), FileFormat=17)
        finally:
            document.Close(False)
    finally:
        word.Quit()


_PS_TEMPLATE = """\
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $null
try {{
    $doc = $word.Documents.Open('{source}')
    $doc.SaveAs('{target}', 17)
}} finally {{
    if ($doc -ne $null) {{ $doc.Close(0) }}
    try {{ $word.Quit() }} catch {{ }}
}}
"""


def _export_with_powershell(source: Path, target: Path) -> None:
    """Export through Word automation driven by a detached PowerShell script."""
    script = _PS_TEMPLATE.format(source=str(source), target=str(target))
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        script_path = Path(tmp) / "export_pdf.ps1"
        script_path.write_text(script, encoding="utf-8-sig")
        for shell in ("pwsh", "powershell"):
            try:
                completed = subprocess.run(
                    [
                        shell,
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(script_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=600,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                failures.append(f"{shell}: {exc}")
                continue
            if completed.returncode == 0:
                return
            message = (completed.stderr or completed.stdout or "").strip()
            failures.append(f"{shell}: {message[:300]}")
    raise RuntimeError("PowerShell/Word export failed: " + " | ".join(failures))


def export_pdf(source: str | Path, target: str | Path) -> int:
    """Export ``source`` to ``target`` and return the verified page count.

    Word's automation interface can raise during shutdown after the file has
    already been written, so the export counts as successful when the produced
    PDF is readable and its page count is positive, no matter what the backend
    reported.
    """
    source = Path(source).resolve()
    target = Path(target).resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    if target.exists():
        target.unlink()

    errors: list[str] = []
    for attempt in (_export_with_python, _export_with_powershell):
        try:
            attempt(source, target)
        except Exception as exc:  # noqa: BLE001 - the file may still exist
            errors.append(f"{attempt.__name__}: {exc}")
        pages = count_pdf_pages(target)
        if pages > 0:
            return pages
    raise RuntimeError("; ".join(errors) or "no PDF backend available")
