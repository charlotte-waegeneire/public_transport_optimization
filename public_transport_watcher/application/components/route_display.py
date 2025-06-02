from typing import Dict, List

import streamlit as st

from public_transport_watcher.application.components.route_map import create_route_map
from public_transport_watcher.predictor.graph_builder import GraphBuilder

_GRAPH_BUILDER = GraphBuilder()
_G = _GRAPH_BUILDER.load_graph("base")


def get_route_summary_short(route_data: Dict) -> str:
    """Generate a short summary of the route."""
    graph_type = route_data.get("graph_type", "unknown")
    route_info = route_data.get("route_info", {})
    travel_time = route_info.get("travel_time_formatted", "N/A")
    num_transfers = route_info.get("num_transfers", 0)

    icon = "🚇" if graph_type == "base" else "⚡"
    type_label = "Standard" if graph_type == "base" else "Optimized"

    transfer_text = (
        f"{num_transfers} correspondance{'s' if num_transfers > 1 else ''}" if num_transfers > 0 else "direct"
    )

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
    walking_dist_start = route_data.get("walking_distance_start", 0)
    walking_time_start = route_data.get("walking_duration_start", 0)

    if walking_dist_start > 0 or walking_time_start > 0:
        walking_dist_formatted = (
            f"{walking_dist_start:.0f}m" if walking_dist_start < 1000 else f"{walking_dist_start / 1000:.1f}km"
        )
        st.markdown(
            f"🚶 **Marcher** {walking_dist_formatted} jusqu'à la première station ({walking_time_start:.0f} min)"
        )


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


def display_station(station: str, index: int, total_stations: int, segments: List[Dict]):
    """Display a single station with appropriate icon, labels, and transfer time."""
    if index == 0:
        station_icon = "🏁"
        station_label = "*(Départ)*"
    elif index == total_stations - 1:
        station_icon = "🎯"
        station_label = "*(Arrivée)*"
    else:
        station_icon = "🚉"
        station_label = ""

    transfer_time = get_transfer_time_for_station(segments, index)
    if transfer_time > 0:
        station_icon = "🔄"
        if station_label:
            station_label = f"{station_label[:-1]} - Correspondance - {transfer_time:.0f} min)*"
        else:
            station_label = f"*(Correspondance - {transfer_time:.0f} min)*"

    st.markdown(f"{station_icon} **{station}** {station_label}")


def display_transport_segment(segment: Dict):
    """Display a transport segment with colored badge - only for actual transport, not transfers."""
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


def get_transfer_time_for_station(segments: List[Dict], station_index: int) -> float:
    """Get the total transfer time for a specific station."""
    transfer_time = 0
    if station_index < len(segments):
        segment = segments[station_index]
        if segment.get("is_transfer", False):
            transfer_time += segment.get("travel_time_mins", 0)
    return transfer_time


def display_route_timeline(route_data: Dict):
    """Display the complete route timeline with stations and segments."""
    route_info = route_data.get("route_info", {})
    segments = route_info.get("segments", [])
    station_names = route_info.get("station_names", [])

    if not segments or not station_names:
        st.error("Aucune information de trajet disponible")
        return

    display_walking_info(route_data)

    station_transfers = {}
    for segment in segments:
        if segment.get("is_transfer", False):
            from_station_id = segment.get("from_station_id")
            transfer_time = segment.get("travel_time_mins", 0)
            if from_station_id not in station_transfers:
                station_transfers[from_station_id] = 0
            station_transfers[from_station_id] += transfer_time

    transport_segments = [seg for seg in segments if not seg.get("is_transfer", False)]

    segment_map = {}
    for segment in transport_segments:
        from_name = segment.get("from_station_name", "")
        to_name = segment.get("to_station_name", "")
        if from_name and to_name:
            segment_map[(from_name, to_name)] = segment

    for station_index, station in enumerate(station_names):
        display_station_with_transfers(station, station_index, len(station_names), station_transfers, route_info)

        if station_index < len(station_names) - 1:
            next_station = station_names[station_index + 1]

            segment = segment_map.get((station, next_station))

            if segment:
                display_transport_segment(segment)
            else:
                found_segment = None
                for seg in transport_segments:
                    from_name = seg.get("from_station_name", "").strip().upper()
                    to_name = seg.get("to_station_name", "").strip().upper()
                    current_station_clean = station.strip().upper()
                    next_station_clean = next_station.strip().upper()

                    if from_name == current_station_clean and to_name == next_station_clean:
                        found_segment = seg
                        break

                if found_segment:
                    display_transport_segment(found_segment)

    walking_dist_end = route_data.get("walking_distance_end", 0)
    walking_time_end = route_data.get("walking_duration_end", 0)

    if walking_dist_end > 0 or walking_time_end > 0:
        walking_dist_formatted = (
            f"{walking_dist_end:.0f}m" if walking_dist_end < 1000 else f"{walking_dist_end / 1000:.1f}km"
        )
        st.markdown(
            f"🚶 **Marcher** {walking_dist_formatted} de la dernière station à la destination ({walking_time_end:.0f} min)"
        )


def display_station_with_transfers(
    station: str, index: int, total_stations: int, station_transfers: Dict, route_info: Dict
):
    """Display a single station with appropriate icon, labels, and transfer time."""
    segments = route_info.get("segments", [])

    station_id = None
    for segment in segments:
        if segment.get("from_station_name") == station:
            station_id = segment.get("from_station_id")
            break
        elif segment.get("to_station_name") == station:
            station_id = segment.get("to_station_id")
            break

    if index == 0:
        station_icon = "🏁"
        station_label = "*(Départ)*"
    elif index == total_stations - 1:
        station_icon = "🎯"
        station_label = "*(Arrivée)*"
    else:
        station_icon = "🚉"
        station_label = ""

    transfer_time = station_transfers.get(station_id, 0) if station_id else 0

    if transfer_time > 0:
        station_icon = "🔄"
        if station_label:
            station_label = f"{station_label[:-1]} - Correspondance - {transfer_time:.0f} min)*"
        else:
            station_label = f"*(Correspondance - {transfer_time:.0f} min)*"

    st.markdown(f"{station_icon} **{station}** {station_label}")


def display_route_info_collapsible(route_data: Dict, route_type: str):
    """Display route information in a collapsible expander."""
    route_summary = get_route_summary_short(route_data)
    transport_summary = get_transport_summary(route_data)
    optimal_path = route_data.get("optimal_path", [])

    with st.expander(f"{route_summary}", expanded=False):
        st.markdown(f"**Transport:** {transport_summary}")
        st.markdown("---")
        route_map = create_route_map(_G, optimal_path, route_data=route_data, auto_zoom=True)
        st.plotly_chart(route_map, use_container_width=True, key=f"route_map_{route_type}")
        display_route_timeline(route_data)


def display_route_results():
    """Display both standard and optimized route results."""
    st.markdown("## 🎯 Vos options de trajet")

    st.markdown("### Trajet standard")
    display_route_info_collapsible(st.session_state.route_data_base, "base")

    if (
        st.session_state.route_data_base["route_info"]["station_names"]
        != st.session_state.route_data_weighted["route_info"]["station_names"]
    ):
        st.markdown("### Avez-vous quelques minutes de plus ? 🕒")
        display_route_info_collapsible(st.session_state.route_data_weighted, "weighted")
