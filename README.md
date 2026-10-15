# PDF Page Splitter & Merger

A small, simple web tool (built with Python + Streamlit) to **split** a PDF by page range and **merge** multiple PDFs into one.
Built for TechAbout — Task 6 (ZR-26-00755).

## What it does

- **Split by page range** – enter ranges like `1-3, 5, 7-9`.
  - Output as *one PDF* with all selected pages, or *a separate PDF per range* (downloaded as a zip).
- **Merge multiple PDFs** – upload 2 or more files, they are merged in the order listed.
- **Clear error messages** for empty files, non-PDF files, corrupted files, password-protected files, and invalid page ranges (backwards, out of range, bad text).
- Files are processed in memory only – nothing is saved on the server.

## Project structure

```
pdf-splitter-merger/
├── app.py                 # Streamlit UI (sky-blue theme)
├── pdf_tools.py           # Core logic: split, merge, validation, error handling
├── tests/test_pdf_tools.py# Automated tests (24 test cases)
├── .streamlit/config.toml # Sky-blue theme colours
├── requirements.txt       # Runtime dependencies (streamlit, pypdf)
├── requirements-dev.txt   # Adds pytest for testing
├── pytest.ini
├── .gitignore
└── README.md
```

## Setup

Requires Python 3.9+.

```bash
# 1. (optional) create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 2. install dependencies
pip install -r requirements.txt

# 3. run the app
streamlit run app.py
```

The app opens at http://localhost:8501.

## How I tested it

Automated tests use `pytest` (PDFs are generated in the tests, so no sample files are needed):

```bash
pip install -r requirements-dev.txt
pytest
```

The suite has 24 test cases covering:

- page-range parsing (single page, ranges, mixed ranges, extra spaces)
- invalid ranges (empty, letters, backwards `5-2`, page beyond the document, `0`)
- split into one file and split into separate files (correct pages, correct order, correct file names)
- merge of 2 and 3 files (page order and page count), and merge with fewer than 2 files
- error handling: empty file, non-PDF file, corrupted PDF, password-protected PDF (split and merge)
- zip output

I also ran the Streamlit app once manually to check the UI for split, merge and error messages.

## Deploy (free live URL)

1. Push this folder to a public GitHub repository.
2. Go to https://share.streamlit.io, sign in with GitHub, click **New app**.
3. Select the repo, branch `main`, main file `app.py`, then **Deploy**.

No secrets or API keys are used, so nothing needs to be configured.

## Limitations

- Password-protected PDFs are rejected (even if you know the password) – remove the password first.
- Pages are split/merged as they are; no rotate, reorder or preview.
- Merge order is the order in which files were uploaded.
- Very large PDFs are limited by Streamlit's upload limit (200 MB by default) and available memory.
- Bookmarks, form fields and other document-level extras may not be preserved after split/merge.
