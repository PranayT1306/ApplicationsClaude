import streamlit as st

st.title("My counter app")

if "count" not in st.session_state:
    st.session_state.count=0

print(st.session_state)
# Buttons
if st.button("➕ Add"):
    st.session_state.count += 1

if st.button("➖ Subtract"):
    st.session_state.count -= 1

if st.button("🔄 Reset"):
    st.session_state.count = 0

# Display
st.write(f"Current count: {st.session_state.count}")