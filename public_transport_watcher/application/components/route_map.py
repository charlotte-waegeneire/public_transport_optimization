from typing import Dict, List, Tuple

import networkx as nx
import plotly.graph_objects as go
import streamlit as st


def get_transport_color(transport_name: str) -> str:
    """Get the same color used in timeline for transport lines"""
    colors = ["#FF6B35", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"]
    return colors[hash(str(transport_name)) % len(colors)]


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
    """Create colored line segments for each transport line"""
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
                    colored_segments.append(
                        {
                            "coords": [(from_lat, from_lon), (to_lat, to_lon)],
                            "transport_name": transport_name,
                            "color": get_transport_color(transport_name),
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
    """Create an interactive map with colored line segments for each transport line"""
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
        print(f"DEBUG: Auto-calculated center: ({center_lat:.4f}, {center_lon:.4f}), zoom: {zoom}")
    else:
        center_lat, center_lon, zoom = fallback_center_lat, fallback_center_lon, fallback_zoom

    fig = go.Figure()

    if route_data:
        colored_segments = create_colored_line_segments(G, optimal_path, route_data)

        for segment in colored_segments:
            lats, lons = zip(*segment["coords"])
            fig.add_trace(
                go.Scattermapbox(
                    lat=lats,
                    lon=lons,
                    mode="lines",
                    line=dict(width=6, color=segment["color"]),
                    name=segment["transport_name"],
                    hoverinfo="skip",
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

    transfer_stations = get_transfer_stations(route_data) if route_data else []

    if station_info:
        start_station = station_info[0]
        end_station = station_info[-1]

        fig.add_trace(
            go.Scattermapbox(
                lat=[start_station["lat"]],
                lon=[start_station["lon"]],
                mode="markers",
                marker=dict(size=15, color="green"),
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
                    marker=dict(size=15, color="red"),
                    text=[f"ARRIVÉE: {end_station['name']}"],
                    hovertemplate="<b>%{text}</b><extra></extra>",
                    name="Arrivée",
                    showlegend=False,
                )
            )

        middle_stations = station_info[1:-1] if len(station_info) > 2 else []

        if middle_stations:
            transfer_lats, transfer_lons, transfer_names = [], [], []
            regular_lats, regular_lons, regular_names = [], [], []

            for station in middle_stations:
                if station["id"] in transfer_stations:
                    transfer_lats.append(station["lat"])
                    transfer_lons.append(station["lon"])
                    transfer_names.append(f"CORRESPONDANCE: {station['name']}")
                else:
                    regular_lats.append(station["lat"])
                    regular_lons.append(station["lon"])
                    regular_names.append(station["name"])

            if transfer_lats:
                fig.add_trace(
                    go.Scattermapbox(
                        lat=transfer_lats,
                        lon=transfer_lons,
                        mode="markers",
                        marker=dict(size=12, color="orange", symbol="diamond"),
                        text=transfer_names,
                        hovertemplate="<b>%{text}</b><extra></extra>",
                        name="Correspondances",
                        showlegend=False,
                    )
                )

            if regular_lats:
                fig.add_trace(
                    go.Scattermapbox(
                        lat=regular_lats,
                        lon=regular_lons,
                        mode="markers",
                        marker=dict(size=8, color="lightblue"),
                        text=regular_names,
                        hovertemplate="<b>%{text}</b><extra></extra>",
                        name="Stations",
                        showlegend=False,
                    )
                )

    fig.update_layout(
        mapbox=dict(style="open-street-map", center=dict(lat=center_lat, lon=center_lon), zoom=zoom),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
    )

    return fig
