import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils import tools_create_item, ask_claude

st.set_page_config(page_title="Create Item", page_icon="➕")
st.title("➕ Create Item")
st.caption("Create inventory items in Oracle EBS via chat")

if "item_messages"        not in st.session_state:
    st.session_state.item_messages        = []
if "item_claude_messages" not in st.session_state:
    st.session_state.item_claude_messages = []

with st.sidebar:
    st.title("🤖 EBS AI Assistant")
    st.success("✅ Oracle Connected")
    st.success("✅ Claude Connected")
    st.markdown("---")
    st.markdown("**📋 Prompt Template**")
    st.caption("Copy, fill in your values, paste in chat")   
         # 1_Create_Item.py sidebar
    template = """Create item with the following details:

        Item Number: 
        Description: 
        Master Org: 
        Child Org: 
        Template: 
        UOM: """
    st.code(template, language=None)


    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state.item_messages        = []
        st.session_state.item_claude_messages = []
        st.rerun()

for msg in st.session_state.item_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("e.g. Create item BEARING-001, Deep Groove Bearing, V1, H1, Purchased Item, EA"):
    st.session_state.item_messages.append({"role": "user", "content": prompt})
    st.session_state.item_claude_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer = ask_claude(st.session_state.item_claude_messages, tools_create_item)
            except Exception as e:
                st.session_state.item_claude_messages = [{"role": "user", "content": prompt}]
                answer = f"⚠️ Error occurred, chat reset. Try again. ({str(e)[:100]})"
            st.markdown(answer)

    st.session_state.item_messages.append({"role": "assistant", "content": answer})
    st.session_state.item_claude_messages.append({"role": "assistant", "content": answer})