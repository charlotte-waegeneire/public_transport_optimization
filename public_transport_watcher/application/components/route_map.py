from typing import List, Tuple

import networkx as nx
import plotly.graph_objects as go
import streamlit as st


def calculate_map_bounds(route_coords: List[Tuple[float, float]], padding: float = 0.005):
    """
    Calculate the optimal center and zoom for the map based on route coordinates
    """
    if not route_coords:
        return 48.8566, 2.3522, 11

    lats, lons = zip(*route_coords)

    min_lat, max_lat = min(lats) - padding, max(lats) + padding
    min_lon, max_lon = min(lons) - padding, max(lons) + padding

    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2

    max_span = max(max_lat - min_lat, max_lon - min_lon)

    zoom_mapping = {
        # key : max span in degrees, value : zoom level
        0.1: 10,
        0.05: 11,
        0.02: 12,
        0.01: 13,
        0.005: 14,
        0: 15,
    }

    zoom = 15
    for span_threshold, zoom_level in zoom_mapping.items():
        if max_span > span_threshold:
            zoom = zoom_level
            break

    return center_lat, center_lon, zoom


def create_route_map(
    G: nx.DiGraph,
    optimal_path: List[int],
    auto_zoom: bool = True,
    fallback_center_lat: float = 48.8566,
    fallback_center_lon: float = 2.3522,
    fallback_zoom: int = 11,
) -> go.Figure:
    """
    Create an interactive map showing the optimal route using Plotly with automatic zoom

    Parameters:
    -----------
    G : networkx.DiGraph
        The transport network graph with node attributes including coordinates
    optimal_path : List[int]
        List of station IDs in the optimal route
    auto_zoom : bool
        Whether to automatically zoom to fit the route (default: True)
    fallback_center_lat : float
        Latitude for map center if auto_zoom is False or route is empty
    fallback_center_lon : float
        Longitude for map center if auto_zoom is False or route is empty
    fallback_zoom : int
        Zoom level if auto_zoom is False or route is empty

    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive map figure
    """
    route_coords = []
    station_info = []

    if not optimal_path:
        st.warning("No route path provided to map. This indicates an issue with route calculation.")
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
            else:
                print(
                    f"WARNING: Station {station_id} missing coordinates. Available attributes: {list(node_data.keys())}"
                )
        else:
            print(f"WARNING: Station {station_id} not found in graph")

    if not route_coords:
        st.error("No coordinates found for route stations. Make sure your graph nodes have coordinate attributes.")
        if G.number_of_nodes() > 0:
            sample_node = list(G.nodes())[0]
            sample_attrs = list(G.nodes[sample_node].keys())
            st.info(f"Available node attributes: {sample_attrs}")
        return go.Figure()

    if auto_zoom and len(route_coords) > 0:
        center_lat, center_lon, zoom = calculate_map_bounds(route_coords)
        print(f"DEBUG: Auto-calculated center: ({center_lat:.4f}, {center_lon:.4f}), zoom: {zoom}")
    else:
        center_lat, center_lon, zoom = fallback_center_lat, fallback_center_lon, fallback_zoom

    fig = go.Figure()

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
        middle_stations = station_info[1:-1] if len(station_info) > 2 else []

        fig.add_trace(
            go.Scattermapbox(
                lat=[start_station["lat"]],
                lon=[start_station["lon"]],
                mode="markers",
                marker=dict(size=15, color="green"),
                text=[f"DÉPART: {start_station['name']}"],
                hovertemplate="<b>%{text}</b><br>Station ID: " + str(start_station["id"]) + "<extra></extra>",
                name="Station de départ",
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
                    hovertemplate="<b>%{text}</b><br>Station ID: " + str(end_station["id"]) + "<extra></extra>",
                    name="Station d'arrivée",
                )
            )

        if middle_stations:
            middle_lats = [s["lat"] for s in middle_stations]
            middle_lons = [s["lon"] for s in middle_stations]
            middle_names = [s["name"] for s in middle_stations]
            middle_ids = [str(s["id"]) for s in middle_stations]

            fig.add_trace(
                go.Scattermapbox(
                    lat=middle_lats,
                    lon=middle_lons,
                    mode="markers",
                    marker=dict(size=10, color="blue"),
                    text=middle_names,
                    customdata=middle_ids,
                    hovertemplate="<b>%{text}</b><br>Station ID: %{customdata}<extra></extra>",
                    name="Stations de la route",
                )
            )

    fig.update_layout(
        mapbox=dict(style="open-street-map", center=dict(lat=center_lat, lon=center_lon), zoom=zoom),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
    )

    return fig
