# pages/6_PDF_to_Table.py

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import base64
import json
import pandas as pd
import io
import fitz  # PyMuPDF — py -m pip install pymupdf
from utils import get_claude_client, save_scrap_to_oracle

st.set_page_config(page_title="PDF to Table", page_icon="📊")
st.title("📊 PDF to Table")
st.caption("Upload a scrap form PDF — Claude extracts the data into an editable table.")

# ── Session State ──────────────────────────────────────────────
if "table_data" not in st.session_state:
    st.session_state.table_data = None
if "table_header" not in st.session_state:
    st.session_state.table_header = None
if "table_pdf_name" not in st.session_state:
    st.session_state.table_pdf_name = None

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.header("📎 Upload Scrap Form PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file and uploaded_file.name != st.session_state.table_pdf_name:
        st.session_state.table_data = None
        st.session_state.table_header = None
        st.session_state.table_pdf_name = uploaded_file.name

    st.divider()
    st.info("""**How it works:**
1. Upload BSDM Scrap Form PDF
2. Click Extract Data
3. Review & correct the table
4. Download as Excel
5. Save to Oracle (coming soon)""")

# ── Main Area ──────────────────────────────────────────────────
# ── Main Area ──────────────────────────────────────────────────
uploaded_file = st.session_state.get("table_pdf_name") and uploaded_file

if uploaded_file is None:
    st.info("👈 Please upload a Scrap Form PDF from the sidebar.")
    st.stop()

st.success(f"📄 File loaded: **{st.session_state.table_pdf_name}**")
# ── Extract Button ─────────────────────────────────────────────
if st.button("🔍 Extract Data from PDF", type="primary"):
    with st.spinner("📄 Converting PDF to images and reading handwriting... please wait"):
        try:
            pdf_bytes = uploaded_file.read()

            # Convert PDF pages to high-res images
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            image_contents = []

            for page in doc:
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for handwriting accuracy
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                img_base64 = base64.standard_b64encode(img_bytes).decode("utf-8")

                image_contents.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_base64,
                    }
                })

            # Add extraction instruction
            image_contents.append({
                "type": "text",
                "text": """Extract all data from this BSDM Manufacturing Scrap Form and return JSON in exactly this format:
{
  "header": {
    "cost_center": "",
    "production_line": "",
    "work_order": "",
    "oracle_item_assembly": "",
    "shift": ""
  },
  "lines": [
    {
      "oracle_item_num": "",
      "item_code": "",
      "description": "",
      "bom_qty": "",
      "scrap_qty": ""
    }
  ]
}

Rules:
- Extract every single line row from the table
- For handwritten SCRAP QTY values, read carefully using surrounding context clues
- If a handwritten value is unclear, add ? after it e.g. "47?"
- Use empty string "" if completely unreadable
- Return raw JSON only — no markdown, no explanation"""
            })

            client = get_claude_client()
            response = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=4096,
                system="You are a data extraction assistant. Extract structured data from manufacturing scrap form images. "
                       "Always respond with valid JSON only — no explanation, no markdown, no code blocks. Just raw JSON.",
                messages=[{"role": "user", "content": image_contents}]
            )

            raw = response.content[0].text.strip()

            # Clean markdown if Claude wrapped it
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            extracted = json.loads(raw)
            st.session_state.table_header = extracted.get("header", {})
            st.session_state.table_data = extracted.get("lines", [])
            st.success("✅ Extraction complete! Review and correct the table below.")

        except json.JSONDecodeError as e:
            st.error(f"Could not parse Claude's response as JSON: {e}")
            st.code(raw, language="json")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ── Display Header ─────────────────────────────────────────────
if st.session_state.table_header:
    st.subheader("📋 Header Information")
    h = st.session_state.table_header
    col1, col2, col3 = st.columns(3)
    col1.metric("Cost Center", h.get("cost_center", "-"))
    col2.metric("Production Line", h.get("production_line", "-"))
    col3.metric("Work Order", h.get("work_order", "-"))
    col4, col5 = st.columns(2)
    col4.metric("Assembly Item", h.get("oracle_item_assembly", "-"))
    col5.metric("Shift", h.get("shift", "-"))

# ── Display Editable Table ─────────────────────────────────────
if st.session_state.table_data:
    st.subheader(f"📦 Extracted Line Items ({len(st.session_state.table_data)} rows)")
    st.info("✏️ Click any cell to correct values — especially handwritten Scrap Qty marked with ?")

    df = pd.DataFrame(st.session_state.table_data)
    df.columns = ["Oracle Item #", "Item Code", "Description", "BOM Qty", "Scrap Qty"]

    # Editable table
    df_edited = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Oracle Item #": st.column_config.TextColumn(width="small"),
            "Item Code": st.column_config.TextColumn(width="medium"),
            "Description": st.column_config.TextColumn(width="large"),
            "BOM Qty": st.column_config.TextColumn(width="small"),
            "Scrap Qty": st.column_config.TextColumn(width="small"),
        }
    )

    st.divider()

    # Download button
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        # Write header info
        header_df = pd.DataFrame([st.session_state.table_header])
        header_df.to_excel(writer, index=False, sheet_name="Header")
        # Write line items
        df_edited.to_excel(writer, index=False, sheet_name="Scrap Lines")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="⬇️ Download as Excel",
            data=buffer.getvalue(),
            file_name=f"scrap_{st.session_state.table_pdf_name}.xlsx",
            mime="application/vnd.ms-excel"
        )

    with col2:
        if st.button("💾 Save to Oracle", type="primary"):
            with st.spinner("Saving to Oracle..."):
                lines = df_edited.to_dict(orient="records")
                result = save_scrap_to_oracle(
                    st.session_state.table_header,
                    lines
                )
                if result["status"] == "S":
                    st.success(f"✅ Saved! Header ID: {result['header_id']} | Lines: {result['lines_inserted']}")
                else:
                    st.error(f"❌ Failed: {result['message']}")