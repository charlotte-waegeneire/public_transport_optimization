from typing import Dict, List

import requests
import streamlit as st
from streamlit_searchbox import st_searchbox

from public_transport_watcher.utils import get_env_variable

_APP_API_ENDPOINT = get_env_variable("APP_API_ENDPOINT")


def search_addresses_api(query: str) -> List[Dict]:
    if not query or len(query.strip()) < 3:
        return []

    try:
        response = requests.get(
            f"{_APP_API_ENDPOINT}/api/v1/routes/search_address_coordinates",
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


def get_route_summary_short(route_data: Dict) -> str:
    graph_type = route_data.get("graph_type", "unknown")
    route_info = route_data.get("route_info", {})
    travel_time = route_info.get("travel_time_formatted", "N/A")
    num_transfers = route_info.get("num_transfers", 0)

    icon = "🚇" if graph_type == "base" else "⚡"
    type_label = "Standard" if graph_type == "base" else "Optimized"

    transfer_text = f"{num_transfers} transfer{'s' if num_transfers > 1 else ''}" if num_transfers > 0 else "direct"

    return f"{icon} **{type_label}** - {travel_time} - {transfer_text}"


def get_transport_summary(route_data: Dict) -> str:
    route_info = route_data.get("route_info", {})
    segments = route_info.get("segments", [])

    transport_names = []
    for segment in segments:
        if not segment.get("is_transfer", False):
            transport_name = segment.get("transport_name", "")
            if transport_name and transport_name not in transport_names:
                transport_names.append(transport_name)

    if not transport_names:
        return "No transport"

    return " → ".join(transport_names)


def display_route_timeline(route_data: Dict):
    route_info = route_data.get("route_info", {})
    segments = route_info.get("segments", [])
    station_names = route_info.get("station_names", [])

    if not segments or not station_names:
        st.error("No route information available")
        return

    walking_dist = route_data.get("walking_distance", 0)
    walking_time = route_data.get("walking_duration", 0)

    if walking_dist > 0:
        walking_dist_formatted = f"{walking_dist:.0f}m" if walking_dist < 1000 else f"{walking_dist / 1000:.1f}km"
        st.markdown(f"🚶 {walking_dist_formatted} walking ({walking_time:.0f} min)")
        st.markdown("")

    if walking_time > 0:
        st.markdown("🚶 **Walk** to the first station")

    transfer_segments = {}
    for i, segment in enumerate(segments):
        if segment.get("is_transfer", False):
            station_index = i + 1
            if station_index not in transfer_segments:
                transfer_segments[station_index] = []
            transfer_segments[station_index].append(segment.get("travel_time_mins", 0))

    for i, station in enumerate(station_names):
        station_icon = "🏁" if i == 0 else "🎯" if i == len(station_names) - 1 else "🚉"
        station_label = "*(Departure)*" if i == 0 else "*(Arrival)*" if i == len(station_names) - 1 else ""

        if i in transfer_segments:
            transfer_times = transfer_segments[i]
            total_transfer_time = sum(transfer_times)
            station_icon = "🔄"
            if station_label == "":
                station_label = f"*(Transfer - {total_transfer_time:.0f} min)*"
            else:
                station_label = f"{station_label[:-1]} - Transfer - {total_transfer_time:.0f} min)*"

        st.markdown(f"{station_icon} **{station}** {station_label}")

        if i < len(segments):
            segment = segments[i]
            travel_time_seg = segment.get("travel_time_mins", 0)
            is_transfer = segment.get("is_transfer", False)
            transport_name = segment.get("transport_name", "")

            if not is_transfer:
                colors = ["#FF6B35", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"]
                color = colors[hash(str(transport_name)) % len(colors)]

                st.markdown(
                    f"""
                &nbsp;&nbsp;&nbsp;&nbsp;
                <span style="
                    background-color: {color}; 
                    color: white; 
                    padding: 2px 8px; 
                    border-radius: 10px; 
                    font-size: 12px;
                    font-weight: bold;
                ">{transport_name}</span> 
                <em>({travel_time_seg:.0f} min)</em>
                """,
                    unsafe_allow_html=True,
                )

    if walking_time > 0:
        st.markdown("🚶 **Walk** from the last station")


def display_route_info(route_data: Dict):
    route_summary = get_route_summary_short(route_data)
    transport_summary = get_transport_summary(route_data)

    st.markdown(f"**{route_summary}**")
    st.markdown(f"**Transport:** {transport_summary}")
    st.markdown("---")
    display_route_timeline(route_data)


def search():
    st.title("🚇 Find your optimal journey")

    if "start_coords" not in st.session_state:
        st.session_state.start_coords = None
    if "end_coords" not in st.session_state:
        st.session_state.end_coords = None
    if "addresses_cache" not in st.session_state:
        st.session_state.addresses_cache = {}
    if "route_data_base" not in st.session_state:
        st.session_state.route_data_base = None
    if "route_data_weighted" not in st.session_state:
        st.session_state.route_data_weighted = None

    # Check if we have results to determine layout
    has_results = st.session_state.route_data_base and st.session_state.route_data_weighted

    # If no results yet, center the search inputs
    if not has_results:
        _, center_col, _ = st.columns([1, 2, 1])
        search_col = center_col
    else:
        # If results exist, split into left (search) and right (results)
        search_col, results_col = st.columns([1, 3], gap="large")

    with search_col:
        st.markdown("### 🏠 Your starting point")

        def search_start_addresses(query: str) -> List[str]:
            addresses = search_addresses_api(query)
            for addr in addresses:
                st.session_state.addresses_cache[addr["address"]] = addr
            return [addr["address"] for addr in addresses]

        start_address = st_searchbox(
            search_function=search_start_addresses,
            placeholder="Type your starting point...",
            label="",
            key="start_search",
            clear_on_submit=False,
        )

        if start_address and start_address in st.session_state.addresses_cache:
            start_address_data = st.session_state.addresses_cache[start_address]
            st.session_state.start_coords = (start_address_data["latitude"], start_address_data["longitude"])
        elif start_address:
            st.session_state.start_coords = None

        st.markdown("---")

        st.markdown("### 🎯 Your destination")

        def search_end_addresses(query: str) -> List[str]:
            addresses = search_addresses_api(query)
            for addr in addresses:
                st.session_state.addresses_cache[addr["address"]] = addr
            return [addr["address"] for addr in addresses]

        end_address = st_searchbox(
            search_function=search_end_addresses,
            placeholder="Type your destination...",
            label="",
            key="end_search",
            clear_on_submit=False,
        )

        if end_address and end_address in st.session_state.addresses_cache:
            end_address_data = st.session_state.addresses_cache[end_address]
            st.session_state.end_coords = (end_address_data["latitude"], end_address_data["longitude"])
        elif end_address:
            st.session_state.end_coords = None

        if st.session_state.start_coords and st.session_state.end_coords:
            if st.button("🔍 Find your optimal journey", type="primary", use_container_width=True):
                with st.spinner("🔍 Finding the optimal route..."):
                    try:
                        response_base = requests.get(
                            f"{_APP_API_ENDPOINT}/api/v1/routes/optimal",
                            params={
                                "start_coords": str(st.session_state.start_coords),
                                "end_coords": str(st.session_state.end_coords),
                            },
                            timeout=10,
                        )

                        response_weighted = requests.get(
                            f"{_APP_API_ENDPOINT}/api/v1/routes/optimal",
                            params={
                                "start_coords": str(st.session_state.start_coords),
                                "end_coords": str(st.session_state.end_coords),
                                "use_weighted": True,
                            },
                            timeout=10,
                        )

                        if response_base.status_code == 200 and response_weighted.status_code == 200:
                            st.session_state.route_data_base = response_base.json()
                            st.session_state.route_data_weighted = response_weighted.json()
                        else:
                            st.error("Failed to find the optimal route, try again later")

                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        st.info("🚧 The optimal route is coming soon!")

    # Display results in the right column when data is available
    if has_results:
        with results_col:
            st.markdown("## 🎯 **Your route options**")

            st.markdown("### Standard Route")
            display_route_info(st.session_state.route_data_base)

            st.markdown("---")

            st.markdown("### Optimized Route")
            display_route_info(st.session_state.route_data_weighted)
