import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
from utils import tools_create_po, ask_claude

st.set_page_config(page_title="Create Purchase Order", page_icon="📋")
st.title("📋 Create Purchase Order")
st.caption("Create Standard Purchase Orders in Oracle EBS via chat")

if "po_messages"        not in st.session_state:
    st.session_state.po_messages        = []
if "po_claude_messages" not in st.session_state:
    st.session_state.po_claude_messages = []

with st.sidebar:
    st.title("🤖 EBS AI Assistant")
    st.success("✅ Oracle Connected")
    st.success("✅ Claude Connected")
    st.markdown("---")
    
    st.markdown("**📋 Prompt Template**")
    st.caption("Copy, fill in your values, paste in chat")
    
    template = """Create a Purchase Order with the following details:

Supplier Number: 
Supplier Site: 
Buyer Employee Number: 
Ship To Location: 
Bill To Location: 
Comments: 

Line 1:
  Item Number: 
  Quantity: 
  Unit Price: 
  Need By Date: YYYY-MM-DD
  Ship To Org: 
  Destination Type: EXPENSE / INVENTORY
  Charge Account: 01-000-XXXX-0000-000"""

    st.code(template, language=None)
    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state.po_messages        = []
        st.session_state.po_claude_messages = []
        st.rerun()

for msg in st.session_state.po_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("e.g. Create PO for supplier 1234, site HYD-MAIN ..."):
    st.session_state.po_messages.append({"role": "user", "content": prompt})
    st.session_state.po_claude_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer = ask_claude(st.session_state.po_claude_messages, tools_create_po)
            except Exception as e:
                st.session_state.po_claude_messages = [{"role": "user", "content": prompt}]
                answer = f"⚠️ Error occurred, chat reset. Try again. ({str(e)[:100]})"
            st.markdown(answer)

    st.session_state.po_messages.append({"role": "assistant", "content": answer})
    st.session_state.po_claude_messages.append({"role": "assistant", "content": answer})