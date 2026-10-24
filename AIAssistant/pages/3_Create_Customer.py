import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils import tools_create_customer, ask_claude

st.set_page_config(page_title="Create Customer", page_icon="➕")
st.title("➕ Create Customer")
st.caption("Onboard new customers into Oracle EBS via chat")

if "cust_messages"        not in st.session_state:
    st.session_state.cust_messages        = []
if "cust_claude_messages" not in st.session_state:
    st.session_state.cust_claude_messages = []

with st.sidebar:
    st.title("🤖 EBS AI Assistant")
    st.success("✅ Oracle Connected")
    st.success("✅ Claude Connected")
    st.markdown("---")
    st.markdown("**📋 Prompt Template**")
    st.caption("Copy, fill in your values, paste in chat")
    
    template = """Create a Customer with the following details:
    
    Customer Name: 
    Address Line 1: 
    Address Line 2: 
    City: 
    State: 
    Postal Code: 
    Country: 
    
    Contact First Name: 
    Contact Last Name: 
    Contact Job Title: 
    Contact Email: 
    Contact Area Code: 
    Contact Phone: """

    st.code(template, language=None)
    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state.cust_messages        = []
        st.session_state.cust_claude_messages = []
        st.rerun()

for msg in st.session_state.cust_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("e.g. Create customer Maruti Suzuki, Plot 1 MG Road ..."):
    st.session_state.cust_messages.append({"role": "user", "content": prompt})
    st.session_state.cust_claude_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer = ask_claude(st.session_state.cust_claude_messages, tools_create_customer)
            except Exception as e:
                st.session_state.cust_claude_messages = [{"role": "user", "content": prompt}]
                answer = f"⚠️ Error occurred, chat reset. Try again. ({str(e)[:100]})"
            st.markdown(answer)

    st.session_state.cust_messages.append({"role": "assistant", "content": answer})
    st.session_state.cust_claude_messages.append({"role": "assistant", "content": answer})