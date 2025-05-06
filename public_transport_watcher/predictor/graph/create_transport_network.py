import networkx as nx
import pandas as pd


def _add_stations_to_graph(G, stations_df):
    for _, station in stations_df.iterrows():
        G.add_node(
            station["id"],
            name=station["name"],
            longitude=station["longitude"],
            latitude=station["latitude"],
            pos=(station["longitude"], station["latitude"]),  # For visualization
        )


def _add_dummy_node(G, station_id):
    G.add_node(
        station_id,
        name=f"Station {station_id}",
        pos=(0, 0),  # Default position
    )


def _add_connections_to_graph(G, schedules_df):
    valid_schedules = schedules_df.copy()
    valid_schedules = valid_schedules[pd.notna(valid_schedules["next_station_id"])]

    for _, schedule in valid_schedules.iterrows():
        from_station = schedule["station_id"]
        to_station = schedule["next_station_id"]

        # Make sure both stations exist in our graph
        if from_station not in G:
            _add_dummy_node(G, from_station)

        if to_station not in G:
            _add_dummy_node(G, to_station)

        # Use travel_time as the weight if available, otherwise use a default value
        weight = schedule["travel_time"] if pd.notna(schedule["travel_time"]) else 5.0

        _add_edge_with_attributes(G, from_station, to_station, schedule, weight)


def _add_edge_with_attributes(G, from_station, to_station, schedule, weight):
    G.add_edge(
        from_station,
        to_station,
        transport_id=schedule["transport_id"],
        journey_id=schedule["journey_id"] if "journey_id" in schedule else None,
        schedule_id=schedule["id"] if "id" in schedule else None,
        timestamp=schedule["timestamp"] if "timestamp" in schedule else None,
        travel_time=weight,  # Store the original travel time
        weight=weight,  # Use travel_time as weight for shortest path algorithms
    )


def create_transport_network(stations_df, schedules_df):
    """
    Create a directed graph representing the transport network where:
    - Nodes are stations with attributes
    - Edges are connections between stations with travel times as weights

    Parameters:
    -----------
    stations_df : pandas DataFrame
        Contains station data (id, name, longitude, latitude)
    schedules_df : pandas DataFrame
        Contains schedule data including travel_time column

    Returns:
    --------
    networkx.DiGraph
        Directed graph representing the transport network with travel times as weights
    """
    G = nx.DiGraph()

    _add_stations_to_graph(G, stations_df)
    _add_connections_to_graph(G, schedules_df)

    return G
