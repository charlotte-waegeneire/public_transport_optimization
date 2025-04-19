import pandas as pd

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_datalake_file

logger = get_logger()


def _extract_gtfs_data() -> dict[str, pd.DataFrame]:
    """
    Loads GTFS data files: stop_times, trips, and calendar.

    Returns a dictionary with the three dataframes.
    """
    try:
        files = get_datalake_file(data_category="schedule", folder="2025", subfolder="april")

        stop_times_file = next(f for f in files if f.endswith("stop_times.txt"))
        trips_file = next(f for f in files if f.endswith("trips.txt"))
        calendar_file = next(f for f in files if f.endswith("calendar.txt"))

        df_stop_times = pd.read_csv(stop_times_file)
        df_trips = pd.read_csv(trips_file)
        df_calendar = pd.read_csv(calendar_file)

        return {"stop_times": df_stop_times, "trips": df_trips, "calendar": df_calendar}

    except (StopIteration, FileNotFoundError, pd.errors.ParserError) as e:
        logger.error(f"Failed to load GTFS data: {e}")
        return {}


def extract_schedule_data() -> pd.DataFrame:
    """
    Processes schedule data from GTFS files and merges them into a single DataFrame.
    Returns a DataFrame with arrival_timestamp, stop_id, and line_numeric_id.
    """
    gtfs_data = _extract_gtfs_data()

    if not gtfs_data:
        logger.warning("No GTFS data available for processing.")
        return pd.DataFrame()

    try:
        df_stop_times = gtfs_data["stop_times"]
        df_trips = gtfs_data["trips"]
        df_calendar = gtfs_data["calendar"]

        # Jointures
        df = df_stop_times.merge(df_trips[["trip_id", "route_id", "service_id"]], on="trip_id", how="left")
        df = df.merge(
            df_calendar[["service_id", "start_date", "end_date"]],
            on="service_id",
            how="left",
        )

        # Conversions
        df["start_date"] = pd.to_datetime(df["start_date"], format="%Y%m%d", errors="coerce")
        df["end_date"] = pd.to_datetime(df["end_date"], format="%Y%m%d", errors="coerce")
        df["arrival_time"] = pd.to_datetime(df["arrival_time"], format="%H:%M:%S", errors="coerce").dt.time

        # Construction du timestamp
        df["service_date"] = df["start_date"]
        df["arrival_timestamp"] = df.apply(
            lambda row: pd.Timestamp.combine(row["service_date"], row["arrival_time"])
            if pd.notnull(row["service_date"]) and pd.notnull(row["arrival_time"])
            else pd.NaT,
            axis=1,
        )

        # Nettoyage des identifiants
        df["line_numeric_id"] = df["trip_id"].str.extract(r"(\d+)").astype(int)
        df["stop_id"] = df["stop_id"].str.extract(r"(\d+)").astype(int)

        # Filtrage des colonnes finales
        df = df[["arrival_timestamp", "stop_id", "line_numeric_id"]].dropna()

        print(df.head())

        return df

    except Exception as e:
        logger.error(f"Failed to process GTFS schedule data: {e}")
        return pd.DataFrame()
