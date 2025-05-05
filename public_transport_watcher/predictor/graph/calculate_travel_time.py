import numpy as np
import pandas as pd


def calculate_travel_time(schedules_df):
    """
    Calculate travel time in minutes between stations based on schedule data

    Parameters:
    -----------
    schedules_df : pandas DataFrame
        Contains schedule data with at least columns: ['transport_id', 'station_id',
        'next_station_id', 'timestamp', 'journey_id']

    Returns:
    --------
    pandas DataFrame
        Original dataframe with added 'travel_time' column (in minutes)
    """
    # Create a copy to avoid modifying the original
    time_travel_df = schedules_df.copy()

    # Drop rows with missing timestamp
    time_travel_df = time_travel_df.dropna(subset=["timestamp"])

    # Ensure timestamp is in datetime format
    time_travel_df["timestamp"] = pd.to_datetime(time_travel_df["timestamp"], format="%H:%M:%S", errors="coerce")

    no_next_station_mask = time_travel_df["next_station_id"].isna()
    time_travel_df.loc[no_next_station_mask, "next_station_id"] = -1
    # station_id and next_station_id are int
    time_travel_df["station_id"] = time_travel_df["station_id"].astype(int)
    time_travel_df["next_station_id"] = time_travel_df["next_station_id"].astype(int)

    time_travel_df = time_travel_df.sort_values(by=["journey_id", "timestamp"])

    # complete the dataframe with the arrival time at next station by shifting timestamp
    # (stays at nan if next station is -1, and has to stay within the same journey_id)
    time_travel_df["arrival_time"] = time_travel_df.groupby("journey_id")["timestamp"].shift(-1)
    time_travel_df.loc[no_next_station_mask, "arrival_time"] = np.nan

    # Calculate travel time and ensure it's positive
    time_travel_df["travel_time"] = (
        (time_travel_df["arrival_time"] - time_travel_df["timestamp"]).dt.total_seconds() / 60
    ) + 1

    # Handle negative travel times:
    # 1. For day transitions (e.g., schedule ends at 23:59 and starts next day at 00:01)
    day_transition_mask = time_travel_df["travel_time"] < 0
    time_travel_df.loc[day_transition_mask, "travel_time"] = (
        (
            time_travel_df.loc[day_transition_mask, "arrival_time"]
            - time_travel_df.loc[day_transition_mask, "timestamp"]
        ).dt.total_seconds()
        / 60
    ) % (24 * 60) + 1  # Add 24 hours (in minutes) for day transitions

    # Ensure all remaining travel times are positive (minimum travel time as 1 minute)
    time_travel_df["travel_time"] = time_travel_df["travel_time"].apply(
        lambda x: max(1.0, x) if pd.notnull(x) else np.nan
    )

    time_travel_df = time_travel_df.dropna(subset=["next_station_id"])
    time_travel_df = time_travel_df.drop_duplicates(
        subset=["journey_id", "transport_id", "station_id", "next_station_id"]
    )

    time_travel_df.loc[time_travel_df["next_station_id"] == -1, "next_station_id"] = np.nan

    # Calculate the mean travel time for each transport-station pair
    time_travel_df["travel_time"] = time_travel_df.groupby(["transport_id", "station_id", "next_station_id"])[
        "travel_time"
    ].transform("mean")
    time_travel_df = time_travel_df.drop_duplicates(subset=["transport_id", "station_id", "next_station_id"])

    return time_travel_df
