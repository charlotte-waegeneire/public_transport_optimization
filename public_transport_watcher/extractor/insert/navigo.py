from datetime import datetime
from typing import Tuple

import pandas as pd
from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import insert as pg_insert

from public_transport_watcher.db.models.transport import (
    Traffic,
    TransportStation,
    TransportTimeBin,
)
from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_engine

logger = get_logger()


def insert_navigo_validations(df: pd.DataFrame, batch_size: int = 10000) -> None:
    """
    Insert Navigo validations data into the database with simplified bulk operations.

    Parameters
    ----------
    df : DataFrame
        Navigo validations data with columns: ida, libelle_arret, jour, tranche_horaire,
        cat_day, validations_horaires
    batch_size : int, optional
        Size of batches for processing data, by default 10000
    """
    engine = get_engine()

    try:
        processed_df = _prepare_data(df)

        total_rows = len(processed_df)
        num_batches = (total_rows + batch_size - 1) // batch_size

        logger.info(f"Processing {total_rows} records in {num_batches} batches")

        for batch_num in range(num_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, total_rows)

            batch_df = processed_df.iloc[start_idx:end_idx]

            with engine.begin() as conn:
                stations_data = batch_df[["station_id", "station_name"]].drop_duplicates()
                _upsert_stations(conn, stations_data)

                time_bins_data = batch_df[["start_timestamp", "end_timestamp", "cat_day"]].drop_duplicates()
                _upsert_time_bins(conn, time_bins_data)

                traffic_data = batch_df[["station_id", "start_timestamp", "end_timestamp", "validations"]]
                _upsert_traffic(conn, traffic_data)

            logger.info(f"Completed batch {batch_num + 1}/{num_batches}")

        logger.info("Successfully inserted all Navigo validations data")

    except Exception as e:
        logger.error(f"Error inserting data: {str(e)}")
        raise


def _prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare and validate the input data."""
    logger.info("Preparing data...")

    processed_df = df.copy()

    processed_df = processed_df.dropna(subset=["ida", "jour", "tranche_horaire", "validations_horaires"])

    processed_df["station_id"] = processed_df["ida"].astype(int)
    processed_df["station_name"] = processed_df["libelle_arret"].astype(str)
    processed_df["validations"] = processed_df["validations_horaires"].astype(float).astype(int)

    timestamps = processed_df.apply(lambda row: _create_timestamps(row["jour"], row["tranche_horaire"]), axis=1)
    processed_df[["start_timestamp", "end_timestamp"]] = pd.DataFrame(timestamps.tolist(), index=processed_df.index)

    logger.info(f"Prepared {len(processed_df)} records")
    return processed_df


def _upsert_stations(conn, stations_df: pd.DataFrame) -> None:
    """Insert or update stations."""
    if stations_df.empty:
        return

    unique_stations = stations_df.drop_duplicates(subset=["station_id"], keep="last")

    stations_data = unique_stations.rename(columns={"station_id": "id", "station_name": "name"}).to_dict("records")

    stmt = pg_insert(TransportStation).values(stations_data)
    stmt = stmt.on_conflict_do_update(index_elements=["id"], set_={"name": stmt.excluded.name})

    conn.execute(stmt)


def _upsert_time_bins(conn, time_bins_df: pd.DataFrame) -> None:
    """Insert time bins, handling duplicates with try/catch."""
    if time_bins_df.empty:
        return

    unique_bins = time_bins_df.drop_duplicates(["start_timestamp", "end_timestamp"], keep="last")

    for _, row in unique_bins.iterrows():
        try:
            stmt = insert(TransportTimeBin).values(row.to_dict())
            conn.execute(stmt)
        except Exception:
            pass


def _upsert_traffic(conn, traffic_df: pd.DataFrame) -> None:
    """Insert or update traffic data."""
    if traffic_df.empty:
        return

    traffic_records = []

    for _, row in traffic_df.iterrows():
        from sqlalchemy import text

        time_bin_query = text(
            """
        SELECT id FROM transport.time_bin 
        WHERE start_timestamp = :start_ts AND end_timestamp = :end_ts
        """
        )

        result = conn.execute(time_bin_query, {"start_ts": row["start_timestamp"], "end_ts": row["end_timestamp"]})
        time_bin_row = result.fetchone()

        if time_bin_row:
            traffic_records.append(
                {"station_id": row["station_id"], "time_bin_id": time_bin_row[0], "validations": row["validations"]}
            )

    if traffic_records:
        try:
            stmt = pg_insert(Traffic).values(traffic_records)
            stmt = stmt.on_conflict_do_update(
                index_elements=["station_id", "time_bin_id"], set_={"validations": stmt.excluded.validations}
            )
            conn.execute(stmt)
        except Exception:
            for record in traffic_records:
                try:
                    stmt = insert(Traffic).values(record)
                    conn.execute(stmt)
                except Exception:
                    pass


def _create_timestamps(date_val: str, time_range_str: str) -> Tuple[datetime, datetime]:
    """Create start and end timestamps from date and time range."""
    if isinstance(date_val, pd.Timestamp):
        date_obj = date_val.to_pydatetime().date()
    else:
        date_obj = datetime.strptime(date_val, "%Y-%m-%d").date()

    start_hour, end_hour = map(int, time_range_str.replace("H", "").split("-"))

    start_timestamp = datetime.combine(date_obj, datetime.min.time()).replace(hour=start_hour)
    end_timestamp = datetime.combine(date_obj, datetime.min.time()).replace(hour=end_hour)

    return start_timestamp, end_timestamp
