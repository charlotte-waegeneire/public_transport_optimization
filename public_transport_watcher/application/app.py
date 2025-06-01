import streamlit as st

st.set_page_config(
    page_title="Find the best route !",
    page_icon="🚌",
    layout="wide",
)

# the previous line codes are needed to avoid streamlit from crashing
from public_transport_watcher.application.pages import search  # noqa: E402

search_page = st.Page(search, title="Search", icon=":material/search:")

pg = st.navigation([search_page])

pg.run()
