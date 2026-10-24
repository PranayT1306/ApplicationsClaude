import streamlit as st
from utils import get_claude_client, get_db_connection, CLAUDE_MODEL, SYSTEM_PROMPT

# These are now one-liners — connection created once, reused everywhere
client = get_claude_client()
conn   = get_db_connection()

st.set_page_config(page_title="EBS AI Assistant", page_icon="🤖")
st.title("🤖 EBS AI Assistant")

# ... rest of your chat UI code