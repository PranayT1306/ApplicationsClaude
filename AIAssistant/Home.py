import streamlit as st

st.set_page_config(
    page_title="Pranay Enterprise AI Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("Pranay Enterprise AI Assistant 🤖")
st.subheader("Master Data Conversion AI Assistant")
st.markdown("---")
st.divider()
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.info("### ➕ Create Item\nCreate inventory items in Oracle EBS")
    st.page_link("pages/1_Create_Item.py", label="Go to Create Item", icon="➕")
with col2:
    st.info("### ➕ Create Supplier\nAdd new suppliers/vendors to Oracle EBS")
    st.page_link("pages/2_Create_Supplier.py", label="Go to Create Supplier", icon="➕")
with col3:
    st.info("### ➕ Create Customer\nOnboard new customers into Oracle EBS")
    st.page_link("pages/3_Create_Customer.py", label="Go to Create Customer", icon="➕")
with col4:
    st.info("### ➕ Create Purchase Orders \nCreate new PO into Oracle EBS")
    st.page_link("pages/4_Create_PO.py", label="Go to Create Purchase Orders", icon="➕")
with col5:
    st.info("### 📄 PDF Assistant \nAsk questions about any PDF document")
    st.page_link("pages/5_PDF_Assistant.py", label="Go to PDF Assistant", icon="📄")

with col6:
    st.info("### 📊 PDF to Table \nExtract scrap form data into Oracle")
    st.page_link("pages/6_PDF_to_Table.py", label="Go to PDF to Table", icon="📊")

st.divider()
st.markdown("---")
st.caption("Use the sidebar to navigate between pages.")