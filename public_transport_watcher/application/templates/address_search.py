from typing import Dict, List

import requests
import streamlit as st
from streamlit_searchbox import st_searchbox


def search_addresses_api(query: str, api_endpoint: str) -> List[Dict]:
    """Search for addresses using the API."""
    if not query or len(query.strip()) < 3:
        return []

    try:
        response = requests.get(
            f"{api_endpoint}/api/v1/routes/search_address_coordinates",
            params={"query": query.strip(), "limit": 10},
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            addresses = data.get("addresses", [])
            return addresses
        else:
            return []

    except Exception:
        return []


def create_search_function(api_endpoint: str):
    """Create a search function that caches results in session state."""

    def search_function(query: str) -> List[str]:
        addresses = search_addresses_api(query, api_endpoint)
        for addr in addresses:
            st.session_state.addresses_cache[addr["address"]] = addr
        return [addr["address"] for addr in addresses]

    return search_function


def create_address_searchbox(search_function, placeholder: str, key: str):
    """Create a standardized address search box."""
    return st_searchbox(
        search_function=search_function,
        placeholder=placeholder,
        label="",
        key=key,
        clear_on_submit=False,
    )


def display_selected_address(address: str):
    """Display the currently selected address."""
    if address:
        st.info(f"📍 Selected: {address}")


def render_address_search_section(title: str, emoji: str, address_type: str, api_endpoint: str, has_results: bool):
    """Render a complete address search section."""
    st.markdown(f"#### {emoji} {title}")

    selected_address = st.session_state.get(f"selected_{address_type}_address", "")
    if selected_address and has_results:
        display_selected_address(selected_address)

    search_function = create_search_function(api_endpoint)

    search_key = f"{address_type}_search_{st.session_state.get('search_reset_counter', 0)}"
    placeholder = f"Type your {title.lower()}..."

    return create_address_searchbox(search_function, placeholder, search_key)
