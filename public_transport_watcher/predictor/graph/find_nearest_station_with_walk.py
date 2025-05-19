from math import asin, cos, radians, sin, sqrt

import networkx as nx


def _haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Earth radius in kilometers
    return c * r * 1000  # meters


def find_nearest_station_with_walk(
    point_lat: float,
    point_lon: float,
    transport_graph: nx.Graph,
    max_distance: float = 10.0,
    walking_speed_kmh: float = 4.5,
) -> dict:
    """
    Find the nearest station and calculate the walking distance/duration.

    Parameters
    ----------
    point_lat: float
        Latitude of the point
    point_lon: float
        Longitude of the point
    transport_graph: networkx.Graph
        Transport graph
    max_distance: float, optional
        Maximum distance to the station (in kilometers)
    walking_speed_kmh: float, optional
        Walking speed (in km/h)

    Returns
    -------
    dict
        Information about the nearest station and walking distance/duration
    """
    nearest = None
    min_distance = float("inf")

    for node_id, data in transport_graph.nodes(data=True):
        if "latitude" in data and "longitude" in data:
            dist = _haversine(point_lat, point_lon, data["latitude"], data["longitude"])
            if dist <= max_distance * 1000 and dist < min_distance:
                min_distance = dist
                nearest = {
                    "station_id": node_id,
                    "name": data.get("name", f"Station {node_id}"),
                    "latitude": data["latitude"],
                    "longitude": data["longitude"],
                    "walking_distance": dist,
                    "walking_duration": (dist / 1000) / walking_speed_kmh * 60,  # minutes
                }

    return nearest
