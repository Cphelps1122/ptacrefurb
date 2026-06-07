import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="PTAC Refurb Marketing OS",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
.block-container {
    padding: 0.5rem 1rem;
    max-width: 1800px;
}
iframe {
    border: none;
}
</style>
""", unsafe_allow_html=True)

st.title("PTAC Refurb Marketing OS")

GOOGLE_SHEET_EMBED_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTErrBGKouHS2uifiw57lwBSTZ_LSTTSqUKHW386FWWi38OYGGcEgN6gOxbpQEgFgZByyfpkfde15aq/pubhtml?gid=380943147&single=true"

components.iframe(
    GOOGLE_SHEET_EMBED_URL,
    height=1100,
    scrolling=True
)
