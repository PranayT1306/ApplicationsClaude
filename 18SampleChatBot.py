import streamlit as st
import anthropic 
import os
import json

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH=os.path.join(BASE_DIR,'json.config')
with open(CONFIG_PATH,'r') as c:
    params=json.load(c)["params"]

try:
    client=anthropic.Anthropic(
        api_key=params["anthropic_api_key"]
    )
    print(f"claude connected")
except Exception as e:
       print(f"unable to connect Claude")

st.title("Claude Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
     with st.chat_message(msg["role"]):
          st.write(msg["content"])

if prompt := st.chat_input("Ask Claude..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Call Claude API
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=st.session_state.messages
    )
    
    reply = response.content[0].text
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()