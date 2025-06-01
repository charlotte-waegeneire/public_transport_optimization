import networkx as nx
import pandas as pd


def adjust_station_weights(
    G: nx.DiGraph,
    frequency_data: pd.DataFrame,
    weight_factor: float = 0.1,
    base_penalty: float = 5.0,
    transfer_multiplier: float = 2.0,
) -> nx.DiGraph:
    """
    Adjust edge weights in the transport network based on station frequency data.

    This function can either modify travel times (original behavior) or add
    congestion penalties to avoid crowded stations, especially for transfers.

    Parameters
    ----------
    G : networkx.DiGraph
        The transport network graph
    frequency_data : pd.DataFrame
        DataFrame with 'station_id' and 'predictions' columns
    weight_factor : float, default=0.1
        Factor to control how much the frequency affects weights (higher means more impact)
    base_penalty : float, default=5.0
        Base penalty (in minutes) for crowded stations when using "penalties" mode
    transfer_multiplier : float, default=2.0
        Multiplier for penalties at transfer stations when using "penalties" mode

    Returns:
    --------
    networkx.DiGraph
        The modified graph with adjusted weights or congestion penalties
    """
    if isinstance(frequency_data, dict):
        frequency_df = pd.DataFrame(
            {"station_id": list(frequency_data.keys()), "predictions": list(frequency_data.values())}
        )
    else:
        frequency_df = frequency_data.copy()
        if "station_id" not in frequency_df.columns or "predictions" not in frequency_df.columns:
            raise ValueError("frequency_data DataFrame must contain 'station_id' and 'predictions' columns")

        if len(frequency_df) > 0 and isinstance(frequency_df["predictions"].iloc[0], (pd.DataFrame, pd.Series)):
            if "total" in frequency_df.columns:
                frequency_df["normalized_predictions"] = frequency_df["total"]
            else:
                frequency_df["normalized_predictions"] = frequency_df["predictions"].apply(
                    lambda x: x["forecast"].sum() if isinstance(x, pd.DataFrame) else x
                )
        else:
            frequency_df["normalized_predictions"] = frequency_df["predictions"]

    if len(frequency_df) > 0:
        min_freq = frequency_df["normalized_predictions"].min()
        max_freq = frequency_df["normalized_predictions"].max()

        if min_freq == max_freq:
            frequency_df["normalized"] = 0.5
        else:
            frequency_df["normalized"] = (frequency_df["normalized_predictions"] - min_freq) / (max_freq - min_freq)

    G_modified = G.copy()

    # Add congestion penalties to stations as node attributes
    crowd_lookup = dict(zip(frequency_df["station_id"], frequency_df["normalized"]))

    # Identify transfer stations (connected to multiple lines)
    transfer_stations = set()
    for node in G_modified.nodes():
        connected_lines = set()

        # Check outgoing edges
        for _, neighbor in G_modified.edges(node):
            edge_data = G_modified[node][neighbor]
            if "line" in edge_data:
                connected_lines.add(edge_data["line"])

        # Check incoming edges
        for neighbor, _ in G_modified.in_edges(node):
            edge_data = G_modified[neighbor][node]
            if "line" in edge_data:
                connected_lines.add(edge_data["line"])

        if len(connected_lines) > 1:
            transfer_stations.add(node)

    # Add penalties to nodes
    for node in G_modified.nodes():
        crowd_level = crowd_lookup.get(node, 0.0)
        penalty = base_penalty * crowd_level

        # Apply transfer multiplier for transfer stations
        if node in transfer_stations:
            penalty *= transfer_multiplier

        G_modified.nodes[node]["congestion_penalty"] = penalty
        G_modified.nodes[node]["crowd_level"] = crowd_level
        G_modified.nodes[node]["is_transfer"] = node in transfer_stations

    # Modify edge weights to include destination station penalties
    for u, v, data in G_modified.edges(data=True):
        original_weight = data.get("weight", 1.0)
        dest_penalty = G_modified.nodes[v].get("congestion_penalty", 0.0)

        # Apply weight_factor to control how much penalty to include
        adjusted_penalty = dest_penalty * weight_factor
        new_weight = original_weight + adjusted_penalty

        G_modified[u][v]["weight"] = new_weight

    return G_modified
