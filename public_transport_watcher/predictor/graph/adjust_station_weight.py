import networkx as nx
import pandas as pd


def adjust_station_weights(
    G: nx.DiGraph,
    frequency_data: pd.DataFrame,
    weight_factor: float = 0.1,
    min_factor: float = 0.5,
    max_factor: float = 1.5,
) -> nx.DiGraph:
    """
    Adjust edge weights in the transport network based on station frequency data.

    This function modifies the weights of edges connected to stations based on
    their frequency of use (number of passengers). Stations with higher frequency
    will have reduced weights (faster travel) while stations with lower frequency
    might have increased weights (slower travel) to reflect congestion or service levels.

    Parameters
    ----------
    G : networkx.DiGraph
        The transport network graph
    frequency_data : pd.DataFrame
        DataFrame with 'station_id' and 'predictions' columns
    weight_factor : float, default=0.1
        Factor to control how much the frequency affects weights (higher means more impact)
    min_factor : float, default=0.5
        Minimum multiplier for weights (prevents weights from becoming too small)
    max_factor : float, default=1.5
        Maximum multiplier for weights (prevents weights from becoming too large)

    Returns:
    --------
    networkx.DiGraph
        The modified graph with adjusted weights
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
            frequency_df["normalized"] = 1 - (
                (frequency_df["normalized_predictions"] - min_freq) / (max_freq - min_freq)
            )

    G_modified = G.copy()

    for u, v, data in G_modified.edges(data=True):
        original_weight = data.get("weight", 1.0)

        source_freq = frequency_df[frequency_df["station_id"] == u]["normalized"].values
        target_freq = frequency_df[frequency_df["station_id"] == v]["normalized"].values

        if len(source_freq) > 0 and len(target_freq) > 0:
            avg_norm_freq = (source_freq[0] + target_freq[0]) / 2
            adjusted_norm_freq = min_factor + (max_factor - min_factor) * avg_norm_freq

            # Apply weight_factor to determine how much of the adjustment to use
            # weight_factor = 0 means no adjustment (factor = 1.0)
            # weight_factor = 1 means full adjustment
            adjustment = 1.0 + (adjusted_norm_freq - 1.0) * weight_factor

        elif len(source_freq) > 0:
            adjusted_norm_freq = min_factor + (max_factor - min_factor) * source_freq[0]
            adjustment = 1.0 + (adjusted_norm_freq - 1.0) * weight_factor

        elif len(target_freq) > 0:
            adjusted_norm_freq = min_factor + (max_factor - min_factor) * target_freq[0]
            adjustment = 1.0 + (adjusted_norm_freq - 1.0) * weight_factor

        else:
            adjustment = 1.0

        new_weight = original_weight * adjustment

        G_modified[u][v]["weight"] = new_weight

    return G_modified
