import networkx as nx
import pandas as pd


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
    # Create an empty directed graph
    G = nx.DiGraph()

    # Add stations as nodes with their attributes
    for _, station in stations_df.iterrows():
        G.add_node(
            station["id"],
            name=station["name"],
            longitude=station["longitude"],
            latitude=station["latitude"],
            pos=(station["longitude"], station["latitude"]),  # For visualization
        )

    # Process schedules to create edges
    valid_schedules = schedules_df.copy()
    valid_schedules = valid_schedules[pd.notna(valid_schedules["next_station_id"])]

    # Add connections as edges
    for _, schedule in valid_schedules.iterrows():
        from_station = schedule["station_id"]
        to_station = schedule["next_station_id"]

        # Make sure both stations exist in our graph
        if from_station not in G:
            # Create a dummy node if the station isn't in our stations_df
            G.add_node(
                from_station,
                name=f"Station {from_station}",
                pos=(0, 0),  # Default position
            )

        if to_station not in G:
            # Create a dummy node if the station isn't in our stations_df
            G.add_node(
                to_station,
                name=f"Station {to_station}",
                pos=(0, 0),  # Default position
            )

        # Use travel_time as the weight if available, otherwise use a default value (5 minutes as fallback)
        weight = schedule["travel_time"] if pd.notna(schedule["travel_time"]) else 5.0

        # Add the edge with all relevant information
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

    return G
