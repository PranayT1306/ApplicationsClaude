import streamlit as st

# Title
st.title("Your App Title")

# Text input
question = st.text_input("Label")

# Button
if st.button("Click me"):
    # do something

# Show data
st.dataframe(df)

# Show code
st.code(sql, language='sql')

# Download button
st.download_button(...)

# Show error
st.error("message")

# Show spinner
with st.spinner("Loading..."):
    # long running code