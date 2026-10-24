# pages/5_PDF_Assistant.py

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import base64
import fitz  # PyMuPDF — py -m pip install pymupdf

from utils import get_claude_client

st.set_page_config(page_title="PDF Assistant", page_icon="📄")
st.title("📄 PDF Assistant")
st.caption("Upload a PDF and ask questions about its content.")

# ── Session State ──────────────────────────────────────────────
if "pdf_messages" not in st.session_state:
    st.session_state.pdf_messages = []
if "pdf_claude_messages" not in st.session_state:
    st.session_state.pdf_claude_messages = []
if "pdf_images" not in st.session_state:
    st.session_state.pdf_images = None
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None
if "pdf_type" not in st.session_state:
    st.session_state.pdf_type = "digital"

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.header("📎 Upload PDF")

    pdf_type = st.radio(
        "PDF Type:",
        ["Digital / Native PDF", "Scanned / Handwritten PDF"],
        help="Digital = ERP exports, reports. Scanned = physical forms, handwritten."
    )
    st.session_state.pdf_type = "scanned" if "Scanned" in pdf_type else "digital"

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file:
        if uploaded_file.name != st.session_state.pdf_name:
            pdf_bytes = uploaded_file.read()

            if st.session_state.pdf_type == "scanned":
                # Convert pages to images for vision-based reading
                with st.spinner("Converting PDF pages to images..."):
                    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    images = []
                    for page in doc:
                        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                        pix = page.get_pixmap(matrix=mat)
                        img_bytes = pix.tobytes("png")
                        img_base64 = base64.standard_b64encode(img_bytes).decode("utf-8")
                        images.append(img_base64)
                    st.session_state.pdf_images = images
            else:
                # Store as base64 document
                st.session_state.pdf_images = [
                    base64.standard_b64encode(pdf_bytes).decode("utf-8")
                ]

            st.session_state.pdf_name = uploaded_file.name
            st.session_state.pdf_messages = []
            st.session_state.pdf_claude_messages = []
            st.success(f"✅ Loaded: {uploaded_file.name}")
        else:
            st.success(f"✅ Loaded: {uploaded_file.name}")

    st.divider()
    st.header("💡 Sample Questions")
    st.code("""Summarize this document.

What are the key points?

List all Items, BOM Quantities, Scrap Quantities


Extract all line items with
quantities .

What action items are mentioned?""", language=None)

    if st.session_state.pdf_messages:
        st.divider()
        if st.button("🗑️ Clear Chat"):
            st.session_state.pdf_messages = []
            st.session_state.pdf_claude_messages = []
            st.rerun()

# ── Main Area ──────────────────────────────────────────────────
if not st.session_state.pdf_images:
    st.info("👈 Please upload a PDF from the sidebar to get started.")
    st.stop()

pdf_type_label = "🖨️ Scanned PDF" if st.session_state.pdf_type == "scanned" else "📄 Digital PDF"
st.success(f"{pdf_type_label} — Active: **{st.session_state.pdf_name}**")

# Display chat history
for msg in st.session_state.pdf_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Ask anything about the PDF...")

if user_input:
    st.session_state.pdf_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build Claude message
    if len(st.session_state.pdf_claude_messages) == 0:
        # First message — attach PDF content
        if st.session_state.pdf_type == "scanned":
            # Send as images (vision mode)
            content = []
            for img_b64 in st.session_state.pdf_images:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_b64,
                    }
                })
            content.append({"type": "text", "text": user_input})
        else:
            # Send as document with cache control (digital PDF)
            content = [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": st.session_state.pdf_images[0],
                    },
                    "cache_control": {"type": "ephemeral"}
                },
                {"type": "text", "text": user_input}
            ]

        user_message = {"role": "user", "content": content}
    else:
        # Subsequent messages — text only
        user_message = {"role": "user", "content": user_input}

    st.session_state.pdf_claude_messages.append(user_message)

    # Call Claude
    with st.chat_message("assistant"):
        with st.spinner("Reading PDF..." if len(st.session_state.pdf_claude_messages) == 1 else "Thinking..."):
            try:
                client = get_claude_client()
                response = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=2048,
                    system="You are a helpful assistant that answers questions based on the provided PDF document. "
                           "Always base your answers on the document content. "
                           "If the answer is not in the document, say so clearly. "
                           "This document may contain handwritten values. "
                           "Read handwritten content carefully using context clues. "
                           "If you are not confident about a handwritten value, flag it clearly "
                           "e.g. 'Scrap Qty appears to be 6 (handwritten — please verify)'. "
                           "Never guess silently — always flag uncertainty.",
                    messages=st.session_state.pdf_claude_messages
                )
                assistant_reply = response.content[0].text
                st.markdown(assistant_reply)

                st.session_state.pdf_messages.append({"role": "assistant", "content": assistant_reply})
                st.session_state.pdf_claude_messages.append({"role": "assistant", "content": assistant_reply})

            except Exception as e:
                st.error(f"Error: {str(e)}")