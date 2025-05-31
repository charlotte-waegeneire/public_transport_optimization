import streamlit as st


def render_page_header():
    """Render the main page header for the search interface."""
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown("<div style='text-align: center; margin: 2rem 0;'>", unsafe_allow_html=True)
        st.markdown("## 🚇 Find your optimal journey")
        st.markdown("</div>", unsafe_allow_html=True)


def render_new_search_button():
    """Render the new search button and handle its click."""
    from .search_state import reset_search_state

    if st.button("🔄 New Search", use_container_width=True):
        reset_search_state()
        st.rerun()


def create_layout_columns(has_results: bool):
    """
    Create the appropriate column layout based on whether we have results.

    Returns:
        Tuple of columns (search_col, results_col) or (search_col, None)
    """
    if not has_results:
        return st.container(), None
    else:
        return st.columns([2, 3], gap="large")
