from typing import Dict, List

import streamlit as st


def get_route_summary_short(route_data: Dict) -> str:
    """Generate a short summary of the route."""
    graph_type = route_data.get("graph_type", "unknown")
    route_info = route_data.get("route_info", {})
    travel_time = route_info.get("travel_time_formatted", "N/A")
    num_transfers = route_info.get("num_transfers", 0)

    icon = "🚇" if graph_type == "base" else "⚡"
    type_label = "Standard" if graph_type == "base" else "Optimized"

    transfer_text = f"{num_transfers} transfer{'s' if num_transfers > 1 else ''}" if num_transfers > 0 else "direct"

    return f"{icon} **{type_label}** - {travel_time} - {transfer_text}"


def get_transport_summary(route_data: Dict) -> str:
    """Generate a summary of transport modes used."""
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


def display_walking_info(route_data: Dict):
    """Display walking distance and time information."""
    walking_dist = route_data.get("walking_distance", 0)
    walking_time = route_data.get("walking_duration", 0)

    if walking_dist > 0:
        walking_dist_formatted = f"{walking_dist:.0f}m" if walking_dist < 1000 else f"{walking_dist / 1000:.1f}km"
        st.markdown(f"🚶 {walking_dist_formatted} walking ({walking_time:.0f} min)")
        st.markdown("")

    if walking_time > 0:
        st.markdown("🚶 **Walk** to the first station")


def get_transfer_segments(segments: List[Dict]) -> Dict[int, List[float]]:
    """Group transfer segments by station index."""
    transfer_segments = {}
    for i, segment in enumerate(segments):
        if segment.get("is_transfer", False):
            station_index = i + 1
            if station_index not in transfer_segments:
                transfer_segments[station_index] = []
            transfer_segments[station_index].append(segment.get("travel_time_mins", 0))
    return transfer_segments


def display_station(station: str, index: int, total_stations: int, transfer_segments: Dict[int, List[float]]):
    """Display a single station with appropriate icon and labels."""
    station_icon = "🏁" if index == 0 else "🎯" if index == total_stations - 1 else "🚉"
    station_label = "*(Departure)*" if index == 0 else "*(Arrival)*" if index == total_stations - 1 else ""

    if index in transfer_segments:
        transfer_times = transfer_segments[index]
        total_transfer_time = sum(transfer_times)
        station_icon = "🔄"
        if station_label == "":
            station_label = f"*(Transfer - {total_transfer_time:.0f} min)*"
        else:
            station_label = f"{station_label[:-1]} - Transfer - {total_transfer_time:.0f} min)*"

    st.markdown(f"{station_icon} **{station}** {station_label}")


def display_transport_segment(segment: Dict):
    """Display a transport segment with colored badge."""
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


def display_route_timeline(route_data: Dict):
    """Display the complete route timeline with stations and segments."""
    route_info = route_data.get("route_info", {})
    segments = route_info.get("segments", [])
    station_names = route_info.get("station_names", [])

    if not segments or not station_names:
        st.error("No route information available")
        return

    display_walking_info(route_data)

    transfer_segments = get_transfer_segments(segments)

    for i, station in enumerate(station_names):
        display_station(station, i, len(station_names), transfer_segments)

        if i < len(segments):
            display_transport_segment(segments[i])

    walking_time = route_data.get("walking_duration", 0)
    if walking_time > 0:
        st.markdown("🚶 **Walk** from the last station")


def display_route_info_collapsible(route_data: Dict, route_type: str):
    """Display route information in a collapsible expander."""
    route_summary = get_route_summary_short(route_data)
    transport_summary = get_transport_summary(route_data)

    with st.expander(f"{route_summary}", expanded=False):
        st.markdown(f"**Transport:** {transport_summary}")
        st.markdown("---")
        display_route_timeline(route_data)


def display_route_results():
    """Display both standard and optimized route results."""
    st.markdown("## 🎯 Your route options")

    st.markdown("### Standard Route")
    display_route_info_collapsible(st.session_state.route_data_base, "standard")

    st.markdown("### Optimized Route")
    display_route_info_collapsible(st.session_state.route_data_weighted, "optimized")
