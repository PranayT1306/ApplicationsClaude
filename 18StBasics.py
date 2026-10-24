import streamlit as st 
st.title("My Chat App")


# Initialize message list in session state
if "messages" not in st.session_state:
    st.session_state.messages = []


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
if prompt:=st.chat_input("Type something"):
    st.session_state.messages.append({"role":"user","content":prompt})
    st.session_state.messages.append({"role": "assistant", "content": f"You said: {prompt}"})
    st.rerun()

