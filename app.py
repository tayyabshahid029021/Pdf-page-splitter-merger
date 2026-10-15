"""Streamlit UI for the PDF Page Splitter & Merger."""
import streamlit as st

from pdf_tools import (
    PdfToolError,
    get_page_count,
    merge_pdfs,
    split_pdf,
    zip_files,
)

st.set_page_config(page_title="PDF Splitter & Merger", page_icon="📄", layout="centered")

# Small touch of sky-blue styling on top of .streamlit/config.toml
st.markdown(
    """
    <style>
    .block-container {max-width: 760px; padding-top: 2rem;}
    h1 {color: #1B6CA8;}
    .stTabs [data-baseweb="tab"] {font-weight: 600;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📄 PDF Page Splitter & Merger")
st.caption("Split a PDF by page range, or merge several PDFs into one. Files are processed in memory and not stored.")

split_tab, merge_tab = st.tabs(["✂️ Split", "🔗 Merge"])

# ----------------------------------------------------------------- SPLIT
with split_tab:
    st.subheader("Split by page range")
    uploaded = st.file_uploader("Upload a PDF", type=["pdf"], key="split_file")

    if uploaded:
        data = uploaded.getvalue()
        try:
            total = get_page_count(data, uploaded.name)
            st.info(f"**{uploaded.name}** has **{total}** page(s).")

            spec = st.text_input("Pages to extract", placeholder="e.g. 1-3, 5, 7-9")
            mode = st.radio(
                "Output",
                ["One PDF with all selected pages", "Separate PDF for each range (zip)"],
            )

            if st.button("Split PDF", type="primary"):
                separate = mode.startswith("Separate")
                files = split_pdf(data, spec, uploaded.name, separate=separate)
                if len(files) == 1:
                    st.session_state["split_out"] = (files[0][0], files[0][1], "application/pdf")
                else:
                    zip_name = uploaded.name.rsplit(".", 1)[0] + "_split.zip"
                    st.session_state["split_out"] = (zip_name, zip_files(files), "application/zip")
                st.success(f"Done! {len(files)} file(s) created.")
        except PdfToolError as err:
            st.session_state.pop("split_out", None)
            st.error(str(err))

        if "split_out" in st.session_state:
            fname, fdata, mime = st.session_state["split_out"]
            st.download_button("⬇️ Download result", fdata, file_name=fname, mime=mime)

# ----------------------------------------------------------------- MERGE
with merge_tab:
    st.subheader("Merge multiple PDFs")
    uploads = st.file_uploader(
        "Upload 2 or more PDFs", type=["pdf"], accept_multiple_files=True, key="merge_files"
    )
    if uploads:
        st.write("Files will be merged in this order:")
        for i, f in enumerate(uploads, 1):
            st.write(f"{i}. {f.name}")

    if st.button("Merge PDFs", type="primary"):
        try:
            merged = merge_pdfs([(f.name, f.getvalue()) for f in uploads or []])
            st.session_state["merge_out"] = merged
            st.success("Merged successfully!")
        except PdfToolError as err:
            st.session_state.pop("merge_out", None)
            st.error(str(err))

    if "merge_out" in st.session_state:
        st.download_button(
            "⬇️ Download merged PDF",
            st.session_state["merge_out"],
            file_name="merged.pdf",
            mime="application/pdf",
        )
