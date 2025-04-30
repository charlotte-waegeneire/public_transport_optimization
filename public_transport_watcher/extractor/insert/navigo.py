from datetime import datetime
from typing import Any, Dict, List, Tuple

import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import sessionmaker

from public_transport_watcher.db.models.transport import (
    Traffic,
    TransportStation,
    TransportTimeBin,
)
from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_engine

logger = get_logger()


def insert_navigo_data(df: pd.DataFrame) -> None:
    """
    Insert Navigo validations data into the database with optimized bulk operations.

    Parameters
    ----------
    df : DataFrame
        Navigo validations data.
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        stations_data = {}
        time_bins_data = []
        time_bin_keys = set()
        traffic_data = []

        for _, row in df.iterrows():
            try:
                station_id = int(row["ida"])
                station_name = row["libelle_arret"]
                stations_data[station_id] = station_name

                start_timestamp, end_timestamp = _create_timestamps(row["jour"], row["tranche_horaire"])
                bin_key = (start_timestamp, end_timestamp)

                if bin_key not in time_bin_keys:
                    time_bin_keys.add(bin_key)
                    time_bins_data.append(
                        {"start_timestamp": start_timestamp, "end_timestamp": end_timestamp, "cat_day": row["cat_day"]}
                    )

                validations_value = int(float(row["validations_horaires"]))
                traffic_data.append(
                    {
                        "station_id": station_id,
                        "start_timestamp": start_timestamp,
                        "end_timestamp": end_timestamp,
                        "validations": validations_value,
                    }
                )

            except Exception as row_error:
                logger.error(f"Error processing row: {row_error}")
                logger.debug(f"Row data: {row}")
                continue

        stations_added = _bulk_upsert_stations(session, stations_data)
        logger.debug(f"Stations inserted/updated: {stations_added}")

        time_bins_map = _bulk_upsert_time_bins(session, time_bins_data)
        logger.debug(f"Time bins processed: {len(time_bins_map)}")

        traffic_records = []
        for record in traffic_data:
            bin_key = (record.pop("start_timestamp"), record.pop("end_timestamp"))
            if bin_key in time_bins_map:
                record["time_bin_id"] = time_bins_map[bin_key]
                traffic_records.append(record)
            else:
                logger.warning(f"No time bin found for {bin_key}")

        traffic_added = _bulk_upsert_traffic(session, traffic_records)
        logger.debug(f"Traffic records inserted/updated: {traffic_added}")

        session.commit()
        logger.info(
            f"Bulk insertion completed: {stations_added} stations, {len(time_bins_map)} time bins, {traffic_added} traffic records"
        )

    except Exception as e:
        session.rollback()
        logger.error(f"Error inserting data: {str(e)}")
        raise
    finally:
        session.close()

    logger.info("Successfully inserted Navigo validations data.")


def _bulk_upsert_stations(session, stations_map: Dict[int, str]) -> int:
    """Upsert stations in bulk and return number of stations processed."""
    if not stations_map:
        return 0

    stations_to_add = [{"id": station_id, "name": station_name} for station_id, station_name in stations_map.items()]

    if not stations_to_add:
        return 0

    stmt = pg_insert(TransportStation).values(stations_to_add)
    stmt = stmt.on_conflict_do_update(index_elements=["id"], set_={"name": stmt.excluded.name})

    result = session.execute(stmt)
    return result.rowcount


def _bulk_upsert_time_bins(session, time_bins_data: List[Dict[str, Any]]) -> Dict[Tuple[datetime, datetime], int]:
    """Upsert time bins in bulk and return mapping of bin_key to time_bin_id."""
    result_dict = {}

    if not time_bins_data:
        return result_dict

    all_start_timestamps = [tb["start_timestamp"] for tb in time_bins_data]
    all_end_timestamps = [tb["end_timestamp"] for tb in time_bins_data]

    existing_time_bins = (
        session.execute(
            select(TransportTimeBin).where(
                (TransportTimeBin.start_timestamp.in_(all_start_timestamps))
                & (TransportTimeBin.end_timestamp.in_(all_end_timestamps))
            )
        )
        .scalars()
        .all()
    )

    for time_bin in existing_time_bins:
        result_dict[(time_bin.start_timestamp, time_bin.end_timestamp)] = time_bin.id

    bins_to_insert = []
    for tb in time_bins_data:
        key = (tb["start_timestamp"], tb["end_timestamp"])
        if key not in result_dict:
            bins_to_insert.append(tb)

    if bins_to_insert:
        stmt = insert(TransportTimeBin).values(bins_to_insert)
        session.execute(stmt)
        session.flush()

        for bin_data in bins_to_insert:
            key = (bin_data["start_timestamp"], bin_data["end_timestamp"])
            if key not in result_dict:
                time_bin = session.execute(
                    select(TransportTimeBin).where(
                        (TransportTimeBin.start_timestamp == key[0]) & (TransportTimeBin.end_timestamp == key[1])
                    )
                ).scalar_one_or_none()

                if time_bin:
                    result_dict[key] = time_bin.id

    return result_dict


def _bulk_upsert_traffic(session, traffic_records: List[Dict[str, Any]]) -> int:
    """Upsert traffic data in bulk and return count of records processed."""
    if not traffic_records:
        return 0

    stmt = pg_insert(Traffic).values(traffic_records)
    stmt = stmt.on_conflict_do_update(
        index_elements=["station_id", "time_bin_id"], set_={"validations": stmt.excluded.validations}
    )

    result = session.execute(stmt)
    return result.rowcount


def _create_timestamps(date_val: str, time_range_str: str) -> Tuple[datetime, datetime]:
    if isinstance(date_val, pd.Timestamp):
        date_obj = date_val.to_pydatetime()
    else:
        date_obj = datetime.strptime(date_val, "%Y-%m-%d")

    start_hour, end_hour = map(int, time_range_str.replace("H", "").split("-"))

    start_timestamp = date_obj.replace(hour=start_hour, minute=0, second=0)
    end_timestamp = date_obj.replace(hour=end_hour, minute=0, second=0)

    return start_timestamp, end_timestamp
