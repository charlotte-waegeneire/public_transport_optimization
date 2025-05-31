"""
Main search interface for the public transport watcher.
"""

from typing import Tuple

import requests
import streamlit as st
from templates.address_search import render_address_search_section
from templates.route_display import display_route_results
from templates.search_state import (
    has_coordinates,
    has_search_results,
    initialize_session_state,
    update_address_selection,
)
from templates.ui_components import create_layout_columns, render_new_search_button, render_page_header

from public_transport_watcher.utils import get_env_variable

_APP_API_ENDPOINT = get_env_variable("APP_API_ENDPOINT")


def fetch_optimal_routes(start_coords: Tuple[float, float], end_coords: Tuple[float, float]) -> Tuple[bool, str]:
    try:
        response_base = requests.get(
            f"{_APP_API_ENDPOINT}/api/v1/routes/optimal",
            params={
                "start_coords": str(start_coords),
                "end_coords": str(end_coords),
            },
            timeout=10,
        )

        # Fetch optimized route
        response_weighted = requests.get(
            f"{_APP_API_ENDPOINT}/api/v1/routes/optimal",
            params={
                "start_coords": str(start_coords),
                "end_coords": str(end_coords),
                "use_weighted": True,
            },
            timeout=10,
        )

        if response_base.status_code == 200 and response_weighted.status_code == 200:
            st.session_state.route_data_base = response_base.json()
            st.session_state.route_data_weighted = response_weighted.json()
            return True, ""
        else:
            return False, "Failed to find the optimal route, try again later"

    except Exception as e:
        return False, f"Error: {str(e)}"


def handle_route_search(has_results: bool):
    button_text = "🔄 Update journey" if has_results else "🔍 Find your optimal journey"

    if st.button(button_text, type="primary", use_container_width=True):
        with st.spinner("🔍 Finding the optimal route..."):
            start_coords = st.session_state.start_coords
            end_coords = st.session_state.end_coords

            success, error_message = fetch_optimal_routes(start_coords, end_coords)

            if success:
                st.rerun()
            else:
                st.error(error_message)
                if "Error:" not in error_message:
                    st.info("🚧 The optimal route is coming soon!")


def search():
    initialize_session_state()

    has_results = has_search_results()

    if not has_results:
        render_page_header()
        search_col, results_col = create_layout_columns(has_results)
    else:
        search_col, results_col = create_layout_columns(has_results)

    with search_col:
        render_search_interface(has_results)

    if has_results and results_col:
        with results_col:
            display_route_results()
            render_new_search_button()


def render_search_interface(has_results: bool):
    start_address = render_address_search_section(
        title="Your starting point",
        emoji="🏠",
        address_type="start",
        api_endpoint=_APP_API_ENDPOINT,
        has_results=has_results,
    )

    if start_address:
        update_address_selection(start_address, "start")

    end_address = render_address_search_section(
        title="Your destination",
        emoji="🎯",
        address_type="end",
        api_endpoint=_APP_API_ENDPOINT,
        has_results=has_results,
    )

    if end_address:
        update_address_selection(end_address, "end")

    if has_coordinates():
        handle_route_search(has_results)
