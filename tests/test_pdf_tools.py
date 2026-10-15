"""Automated tests for pdf_tools. Run with:  pytest"""
import io
import zipfile

import pytest
from pypdf import PdfReader, PdfWriter

from pdf_tools import (
    PdfToolError,
    get_page_count,
    merge_pdfs,
    parse_page_ranges,
    split_pdf,
    zip_files,
)


def make_pdf(pages, base_width=200, password=None):
    """Build a PDF where page i has width base_width + i (so pages can be told apart)."""
    writer = PdfWriter()
    for i in range(pages):
        writer.add_blank_page(width=base_width + i, height=300)
    if password:
        writer.encrypt(password)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def widths(pdf_bytes):
    return [int(p.mediabox.width) for p in PdfReader(io.BytesIO(pdf_bytes)).pages]


# ---------------------------------------------------------- range parsing
def test_parse_single_page_and_range():
    assert parse_page_ranges("3", 10) == [(3, 3)]
    assert parse_page_ranges("2-5", 10) == [(2, 5)]


def test_parse_mixed_ranges_with_spaces():
    assert parse_page_ranges(" 1-3, 5 ,7-9 ", 10) == [(1, 3), (5, 5), (7, 9)]


@pytest.mark.parametrize("bad", ["", "   ", "abc", "1-", "-3", "1,,2", "1--3", "0"])
def test_parse_invalid_text_raises(bad):
    with pytest.raises(PdfToolError):
        parse_page_ranges(bad, 10)


def test_parse_out_of_range_and_backwards():
    with pytest.raises(PdfToolError, match="does not exist"):
        parse_page_ranges("1-11", 10)
    with pytest.raises(PdfToolError, match="backwards"):
        parse_page_ranges("5-2", 10)


# ------------------------------------------------------------------ split
def test_split_selected_pages_into_one_file():
    pdf = make_pdf(6)  # widths 200..205
    out = split_pdf(pdf, "2-3, 6", "book.pdf")
    assert len(out) == 1
    assert out[0][0] == "book_selected.pdf"
    assert widths(out[0][1]) == [201, 202, 205]


def test_split_separate_file_per_range():
    pdf = make_pdf(6)
    out = split_pdf(pdf, "1-2, 5", "book.pdf", separate=True)
    assert [name for name, _ in out] == ["book_pages_1-2.pdf", "book_pages_5.pdf"]
    assert widths(out[0][1]) == [200, 201]
    assert widths(out[1][1]) == [204]


def test_split_full_range_keeps_all_pages():
    pdf = make_pdf(4)
    out = split_pdf(pdf, "1-4")
    assert widths(out[0][1]) == [200, 201, 202, 203]


def test_split_page_beyond_document_raises():
    with pytest.raises(PdfToolError, match="only 3 page"):
        split_pdf(make_pdf(3), "2-9")


# ------------------------------------------------------------------ merge
def test_merge_two_files_keeps_order():
    a = make_pdf(2, base_width=200)  # 200, 201
    b = make_pdf(3, base_width=400)  # 400, 401, 402
    merged = merge_pdfs([("a.pdf", a), ("b.pdf", b)])
    assert widths(merged) == [200, 201, 400, 401, 402]


def test_merge_three_files_page_count():
    files = [(f"f{i}.pdf", make_pdf(i + 1)) for i in range(3)]  # 1 + 2 + 3 pages
    assert len(PdfReader(io.BytesIO(merge_pdfs(files))).pages) == 6


def test_merge_needs_at_least_two_files():
    with pytest.raises(PdfToolError, match="at least 2"):
        merge_pdfs([("a.pdf", make_pdf(1))])
    with pytest.raises(PdfToolError, match="at least 2"):
        merge_pdfs([])


# ------------------------------------------------- invalid / protected files
def test_empty_file_error():
    with pytest.raises(PdfToolError, match="empty"):
        split_pdf(b"", "1", "empty.pdf")


def test_not_a_pdf_error():
    with pytest.raises(PdfToolError, match="not a valid PDF"):
        get_page_count(b"hello, I am a text file", "notes.pdf")


def test_corrupted_pdf_error():
    broken = b"%PDF-1.4\nthis is garbage and not a real pdf structure"
    with pytest.raises(PdfToolError, match="corrupted"):
        split_pdf(broken, "1", "broken.pdf")


def test_protected_pdf_error_on_split():
    locked = make_pdf(3, password="secret")
    with pytest.raises(PdfToolError, match="password-protected"):
        split_pdf(locked, "1", "locked.pdf")


def test_protected_pdf_error_on_merge_names_the_file():
    locked = make_pdf(2, password="secret")
    with pytest.raises(PdfToolError, match="locked.pdf"):
        merge_pdfs([("ok.pdf", make_pdf(1)), ("locked.pdf", locked)])


# ------------------------------------------------------------------ misc
def test_zip_files_contains_all_outputs():
    data = zip_files([("a.pdf", b"1"), ("b.pdf", b"2")])
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        assert sorted(zf.namelist()) == ["a.pdf", "b.pdf"]
