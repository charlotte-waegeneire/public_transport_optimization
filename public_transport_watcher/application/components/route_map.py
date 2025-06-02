from typing import Dict, List, Tuple

import networkx as nx
import plotly.graph_objects as go
import streamlit as st

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils.get_transports_icons import ParisTransportMapping, extract_line_code_from_text

logger = get_logger()


def get_transport_color(transport_name: str) -> str:
    """Get the official Paris transport color for a line, with fallback to hash-based colors"""
    line_code = extract_line_code_from_text(transport_name)
    if line_code:
        official_color = ParisTransportMapping.get_line_color(line_code)
        if official_color:
            return official_color

    logger.error(f"No official color found for {transport_name}")
    return


def get_transfer_stations(route_data: Dict) -> List[int]:
    """Get list of station IDs that are transfer points"""
    if not route_data:
        return []

    segments = route_data.get("route_info", {}).get("segments", [])
    transfer_stations = []

    for segment in segments:
        if segment.get("is_transfer", False):
            station_id = segment.get("from_station_id")
            if station_id and station_id not in transfer_stations:
                transfer_stations.append(station_id)

    return transfer_stations


def create_colored_line_segments(G: nx.DiGraph, optimal_path: List[int], route_data: Dict):
    """Create colored line segments for each transport line using official Paris transport colors"""
    if not route_data:
        return []

    segments = route_data.get("route_info", {}).get("segments", [])
    colored_segments = []

    for segment in segments:
        if not segment.get("is_transfer", False):  # Skip transfer segments
            from_station_id = segment.get("from_station_id")
            to_station_id = segment.get("to_station_id")
            transport_name = segment.get("transport_name", "")

            if from_station_id in G.nodes and to_station_id in G.nodes:
                from_node = G.nodes[from_station_id]
                to_node = G.nodes[to_station_id]

                from_lat, from_lon = from_node.get("lat"), from_node.get("lon")
                to_lat, to_lon = to_node.get("lat"), to_node.get("lon")

                if all([from_lat, from_lon, to_lat, to_lon]):
                    official_color = get_transport_color(transport_name)

                    colored_segments.append(
                        {
                            "coords": [(from_lat, from_lon), (to_lat, to_lon)],
                            "transport_name": transport_name,
                            "color": official_color,
                        }
                    )

    return colored_segments


def calculate_map_bounds(route_coords: List[Tuple[float, float]], padding: float = 0.005):
    """Calculate the optimal center and zoom for the map based on route coordinates"""
    if not route_coords:
        return 48.8566, 2.3522, 11

    lats, lons = zip(*route_coords)
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    lat_padding = max((max_lat - min_lat) * 0.1, padding)
    lon_padding = max((max_lon - min_lon) * 0.1, padding)

    min_lat -= lat_padding
    max_lat += lat_padding
    min_lon -= lon_padding
    max_lon += lon_padding

    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2

    lat_span = max_lat - min_lat
    lon_span = max_lon - min_lon
    max_span = max(lat_span, lon_span)

    if max_span > 0.15:
        zoom = 10
    elif max_span > 0.08:
        zoom = 11
    elif max_span > 0.04:
        zoom = 12
    elif max_span > 0.02:
        zoom = 13
    elif max_span > 0.01:
        zoom = 14
    elif max_span > 0.005:
        zoom = 15
    else:
        zoom = 16

    return center_lat, center_lon, zoom


def create_route_map(
    G: nx.DiGraph,
    optimal_path: List[int],
    route_data: Dict = None,
    auto_zoom: bool = True,
    fallback_center_lat: float = 48.8566,
    fallback_center_lon: float = 2.3522,
    fallback_zoom: int = 11,
) -> go.Figure:
    """Create an interactive map with colored line segments using official Paris transport colors"""
    route_coords = []
    station_info = []

    if not optimal_path:
        st.warning("No route path provided to map.")
        return go.Figure()

    for station_id in optimal_path:
        if station_id in G.nodes:
            node_data = G.nodes[station_id]
            lat, lon = node_data.get("lat"), node_data.get("lon")

            if lat is not None and lon is not None:
                route_coords.append((lat, lon))
                station_info.append(
                    {"id": station_id, "name": node_data.get("name", f"Station {station_id}"), "lat": lat, "lon": lon}
                )

    if not route_coords:
        st.error("No coordinates found for route stations.")
        return go.Figure()

    if auto_zoom and len(route_coords) > 0:
        center_lat, center_lon, zoom = calculate_map_bounds(route_coords)
    else:
        center_lat, center_lon, zoom = fallback_center_lat, fallback_center_lon, fallback_zoom

    fig = go.Figure()

    if route_data:
        colored_segments = create_colored_line_segments(G, optimal_path, route_data)

        transport_lines = {}
        for segment in colored_segments:
            transport_name = segment["transport_name"]
            if transport_name not in transport_lines:
                transport_lines[transport_name] = {"coords": [], "color": segment["color"]}
            transport_lines[transport_name]["coords"].extend(segment["coords"])

        for transport_name, line_data in transport_lines.items():
            if line_data["coords"]:
                lats, lons = zip(*line_data["coords"])
                fig.add_trace(
                    go.Scattermapbox(
                        lat=lats,
                        lon=lons,
                        mode="lines",
                        line=dict(width=5, color=line_data["color"]),
                        name=transport_name,
                        hoverinfo="name",
                        showlegend=False,
                    )
                )
    else:
        if len(route_coords) > 1:
            lats, lons = zip(*route_coords)
            fig.add_trace(
                go.Scattermapbox(
                    lat=lats, lon=lons, mode="lines", line=dict(width=4, color="blue"), name="Route", hoverinfo="skip"
                )
            )

    if station_info:
        start_station = station_info[0]
        end_station = station_info[-1]

        fig.add_trace(
            go.Scattermapbox(
                lat=[start_station["lat"]],
                lon=[start_station["lon"]],
                mode="markers",
                marker=dict(size=18, color="green", symbol="circle"),
                text=[f"DÉPART: {start_station['name']}"],
                hovertemplate="<b>%{text}</b><extra></extra>",
                name="Départ",
                showlegend=False,
            )
        )

        if len(station_info) > 1:
            fig.add_trace(
                go.Scattermapbox(
                    lat=[end_station["lat"]],
                    lon=[end_station["lon"]],
                    mode="markers",
                    marker=dict(size=18, color="red", symbol="circle"),
                    text=[f"ARRIVÉE: {end_station['name']}"],
                    hovertemplate="<b>%{text}</b><extra></extra>",
                    name="Arrivée",
                    showlegend=False,
                )
            )

    fig.update_layout(
        mapbox=dict(style="open-street-map", center=dict(lat=center_lat, lon=center_lon), zoom=zoom),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        hovermode="closest",
    )

    return fig
