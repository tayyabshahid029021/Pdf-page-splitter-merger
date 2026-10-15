"""Core PDF split / merge logic.

No UI code lives here, which keeps the functions simple to test and reuse.
All functions work with raw ``bytes`` and raise ``PdfToolError`` with a
human-friendly message when something is wrong.
"""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import PurePath
from typing import List, Sequence, Tuple

from pypdf import PdfReader, PdfWriter


class PdfToolError(Exception):
    """Raised with a clear, user-friendly message."""


# --------------------------------------------------------------------------
# Opening / validating
# --------------------------------------------------------------------------
def open_pdf(data: bytes, name: str = "file") -> PdfReader:
    """Validate ``data`` and return a ``PdfReader``.

    Raises PdfToolError for empty, non-PDF, corrupted, protected
    (password-encrypted) or zero-page files.
    """
    if not data:
        raise PdfToolError(f"'{name}' is empty (0 bytes).")
    if b"%PDF-" not in data[:1024]:
        raise PdfToolError(f"'{name}' is not a valid PDF file.")
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception:
        raise PdfToolError(f"'{name}' looks corrupted and could not be read.") from None
    if reader.is_encrypted:
        raise PdfToolError(
            f"'{name}' is password-protected. Remove the password and try again."
        )
    try:
        page_count = len(reader.pages)
    except Exception:
        raise PdfToolError(f"'{name}' looks corrupted and could not be read.") from None
    if page_count == 0:
        raise PdfToolError(f"'{name}' has no pages.")
    return reader


def get_page_count(data: bytes, name: str = "file") -> int:
    return len(open_pdf(data, name).pages)


# --------------------------------------------------------------------------
# Page range parsing
# --------------------------------------------------------------------------
def parse_page_ranges(spec: str, total_pages: int) -> List[Tuple[int, int]]:
    """Turn ``"1-3, 5, 7-9"`` into ``[(1, 3), (5, 5), (7, 9)]`` (1-based, inclusive)."""
    cleaned = (spec or "").replace(" ", "")
    if not cleaned:
        raise PdfToolError("Please enter a page range, for example: 1-3, 5, 7-9")

    ranges: List[Tuple[int, int]] = []
    for part in cleaned.split(","):
        if not part:
            raise PdfToolError("Page range has an extra comma. Example: 1-3, 5, 7-9")
        match = re.fullmatch(r"(\d+)(?:-(\d+))?", part)
        if not match:
            raise PdfToolError(
                f"'{part}' is not a valid page range. Use numbers like 3 or 2-6."
            )
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        if start < 1 or end < 1:
            raise PdfToolError("Page numbers start at 1.")
        if start > end:
            raise PdfToolError(f"Range '{part}' is backwards. Use {end}-{start} instead.")
        if end > total_pages:
            raise PdfToolError(
                f"Page {end} does not exist. The PDF has only {total_pages} page(s)."
            )
        ranges.append((start, end))
    return ranges


# --------------------------------------------------------------------------
# Split
# --------------------------------------------------------------------------
def _write(pages) -> bytes:
    writer = PdfWriter()
    for page in pages:
        writer.add_page(page)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def split_pdf(
    data: bytes,
    spec: str,
    name: str = "document.pdf",
    separate: bool = False,
) -> List[Tuple[str, bytes]]:
    """Extract pages from a PDF.

    separate=False -> one PDF containing every selected page (in the order typed).
    separate=True  -> one PDF per range.
    Returns a list of ``(filename, pdf_bytes)``.
    """
    reader = open_pdf(data, name)
    ranges = parse_page_ranges(spec, len(reader.pages))
    stem = PurePath(name).stem or "document"

    if not separate:
        pages = [reader.pages[i - 1] for s, e in ranges for i in range(s, e + 1)]
        return [(f"{stem}_selected.pdf", _write(pages))]

    results = []
    for s, e in ranges:
        label = f"{s}" if s == e else f"{s}-{e}"
        pages = [reader.pages[i - 1] for i in range(s, e + 1)]
        results.append((f"{stem}_pages_{label}.pdf", _write(pages)))
    return results


# --------------------------------------------------------------------------
# Merge
# --------------------------------------------------------------------------
def merge_pdfs(files: Sequence[Tuple[str, bytes]]) -> bytes:
    """Merge ``[(name, bytes), ...]`` into one PDF, keeping the given order."""
    if len(files) < 2:
        raise PdfToolError("Please upload at least 2 PDF files to merge.")
    writer = PdfWriter()
    for name, data in files:
        reader = open_pdf(data, name)
        for page in reader.pages:
            writer.add_page(page)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


# --------------------------------------------------------------------------
# Helper: bundle several outputs into a zip
# --------------------------------------------------------------------------
def zip_files(files: Sequence[Tuple[str, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files:
            zf.writestr(name, data)
    return buffer.getvalue()
