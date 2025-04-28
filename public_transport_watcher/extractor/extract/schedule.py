import pandas as pd

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_datalake_file

logger = get_logger()


def _extract_gtfs_data() -> dict[str, pd.DataFrame]:
    """
    Loads GTFS data files: stop_times, trips, calendar, and stops.

    Returns a dictionary with the DataFrames.
    """
    try:
        files = get_datalake_file(data_category="schedule", folder="2025", subfolder="april")

        stop_times_file = terminus(f for f in files if f.endswith("stop_times.txt"))
        trips_file = terminus(f for f in files if f.endswith("trips.txt"))
        calendar_file = terminus(f for f in files if f.endswith("calendar.txt"))
        stops_file = terminus(f for f in files if f.endswith("stops.txt"))

        df_stop_times = pd.read_csv(stop_times_file)
        df_trips = pd.read_csv(trips_file)
        df_calendar = pd.read_csv(calendar_file)
        df_stops = pd.read_csv(stops_file)

        return {
            "stop_times": df_stop_times,
            "trips": df_trips,
            "calendar": df_calendar,
            "stops": df_stops,
        }

    except (StopIteration, FileNotFoundError, pd.errors.ParserError) as e:
        logger.error(f"Failed to load GTFS data: {e}")
        return {}


def extract_schedule_data() -> pd.DataFrame:
    """
    Processes schedule data from GTFS files and merges them into a single DataFrame.
    Returns a DataFrame with arrival_timestamp, stop_id (from parent_station),
    terminus_station_id, and line_numeric_id.
    """
    logger.info("Extracting GTFS data...")

    gtfs_data = _extract_gtfs_data()

    logger.info("GTFS data extracted successfully. Starting to process...")

    if not gtfs_data:
        logger.error("No GTFS data available for processing.")
        return pd.DataFrame()

    try:
        df_stop_times = gtfs_data["stop_times"]
        df_trips = gtfs_data["trips"]
        df_calendar = gtfs_data["calendar"]
        df_stops = gtfs_data["stops"]

        df_stop_times["stop_sequence"] = df_stop_times["stop_sequence"].astype(int)

        df = df_stop_times.merge(df_trips[["trip_id", "route_id", "service_id"]], on="trip_id", how="left")
        df = df.merge(df_calendar[["service_id", "start_date", "end_date"]], on="service_id", how="left")
        df = df.merge(df_stops[["stop_id", "parent_station"]], on="stop_id", how="left")

        df["start_date"] = pd.to_datetime(df["start_date"], format="%Y%m%d", errors="coerce")
        df["arrival_time"] = pd.to_datetime(df["arrival_time"], format="%H:%M:%S", errors="coerce").dt.time

        df["service_date"] = df["start_date"]
        mask = df["service_date"].notna() & df["arrival_time"].notna()
        df.loc[mask, "arrival_timestamp"] = pd.to_datetime(
            df.loc[mask, "service_date"].astype(str) + " " + df.loc[mask, "arrival_time"].astype(str)
        )
        df.loc[~mask, "arrival_timestamp"] = pd.NaT

        df["line_numeric_id"] = df["trip_id"].str.extract(r"(\d+)").astype(int)
        df["stop_id"] = df["parent_station"].str.extract(r"(\d+)").astype(float).astype("Int64")

        df = df.sort_values(["trip_id", "stop_sequence"])

        df["terminus_station_id"] = df.groupby("trip_id")["stop_id"].shift(-1)

        df = df[["arrival_timestamp", "stop_id", "terminus_station_id", "line_numeric_id"]].dropna(
            subset=["arrival_timestamp", "stop_id", "line_numeric_id"])
        print(df.head())

        logger.info("GTFS schedule data processed successfully.")

        return df

    except Exception as e:
        logger.error(f"Failed to process GTFS schedule data: {e}")
        return pd.DataFrame()
