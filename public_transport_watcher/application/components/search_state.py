import streamlit as st


def initialize_session_state():
    """Initialize all session state variables with default values."""
    defaults = {
        "start_coords": None,
        "end_coords": None,
        "addresses_cache": {},
        "route_data_base": None,
        "route_data_weighted": None,
        "selected_start_address": "",
        "selected_end_address": "",
        "search_reset_counter": 0,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def has_search_results() -> bool:
    """Check if we have both route results."""
    return (
        st.session_state.get("route_data_base") is not None and st.session_state.get("route_data_weighted") is not None
    )


def has_coordinates() -> bool:
    """Check if we have both start and end coordinates."""
    return st.session_state.get("start_coords") is not None and st.session_state.get("end_coords") is not None


def reset_search_state():
    """Reset search-related state for a new search."""
    st.session_state.route_data_base = None
    st.session_state.route_data_weighted = None
    st.session_state.selected_start_address = ""
    st.session_state.selected_end_address = ""
    st.session_state.start_coords = None
    st.session_state.end_coords = None
    st.session_state.search_reset_counter += 1


def update_address_selection(address: str, address_type: str):
    """Update session state when an address is selected."""
    if address and address in st.session_state.addresses_cache:
        address_data = st.session_state.addresses_cache[address]
        coords = (address_data["latitude"], address_data["longitude"])

        if address_type == "start":
            st.session_state.start_coords = coords
            st.session_state.selected_start_address = address
        elif address_type == "end":
            st.session_state.end_coords = coords
            st.session_state.selected_end_address = address
    else:
        if address_type == "start":
            st.session_state.start_coords = None
            st.session_state.selected_start_address = address or ""
        elif address_type == "end":
            st.session_state.end_coords = None
            st.session_state.selected_end_address = address or ""
