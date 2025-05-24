import streamlit as st

from public_transport_watcher.application.pages import search

st.title("Find the best route !")

search_page = st.Page(search, title="Search", icon=":material/search:")

pg = st.navigation([search_page])

pg.run()
