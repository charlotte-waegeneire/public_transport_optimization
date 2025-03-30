from typing import Tuple, List, Dict, Any
from datetime import datetime

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert

from public_transport_watcher.db.models.transport import (
    TransportStation,
    TransportTimeBin,
    Traffic,
)
from public_transport_watcher.logging_config import configure_logging
from public_transport_watcher.utils import get_engine

logger = configure_logging()


def insert_navigo_data(df: pd.DataFrame) -> None:
    """
    Insert Navigo validations data into the database with bulk operations.

    Parameters
    ----------
    df : DataFrame
        Navigo validations data.
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        stations_map = {}
        time_bins_map = {}
        traffic_records = []

        for _, row in df.iterrows():
            try:
                station_id = int(row["ida"])
                station_name = row["libelle_arret"]
                stations_map[station_id] = station_name

                start_timestamp, end_timestamp = _create_timestamps(
                    row["jour"], row["tranche_horaire"]
                )
                bin_key = (start_timestamp, end_timestamp)
                if bin_key not in time_bins_map:
                    time_bins_map[bin_key] = row["cat_day"]

                validations_value = int(float(row["validations_horaires"]))
                traffic_records.append(
                    {
                        "station_id": station_id,
                        "bin_key": bin_key,
                        "validations": validations_value,
                    }
                )

            except Exception as row_error:
                logger.error(f"Error processing row: {row_error}")
                logger.debug(f"Row data: {row}")
                continue

        stations_added = _bulk_process_stations(session, stations_map)

        time_bins_dict = _bulk_process_time_bins(session, time_bins_map)

        for record in traffic_records:
            bin_key = record.pop("bin_key")
            record["time_bin_id"] = time_bins_dict[bin_key]

        traffic_added = _bulk_process_traffic(
            session, traffic_records, bulk_size=1000
        )

        session.commit()

        logger.info(
            f"Bulk insertion completed: {stations_added} stations, {len(time_bins_dict)} time bins, {traffic_added} traffic records"
        )

    except Exception as e:
        session.rollback()
        logger.error(f"Error inserting data: {str(e)}")
        raise
    finally:
        session.close()

    logger.info("Successfully inserted Navigo validations data.")


def _bulk_process_stations(session, stations_map: Dict[int, str]) -> int:
    """Process stations in bulk and return number of new stations added."""
    if not stations_map:
        return 0

    existing_stations = (
        session.execute(
            select(TransportStation).where(
                TransportStation.id.in_(list(stations_map.keys()))
            )
        )
        .scalars()
        .all()
    )

    existing_ids = {station.id for station in existing_stations}

    stations_to_add = []
    for station_id, station_name in stations_map.items():
        if station_id not in existing_ids:
            stations_to_add.append({"id": station_id, "name": station_name})

    if stations_to_add:
        session.execute(insert(TransportStation).values(stations_to_add))
        session.flush()

    return len(stations_to_add)


def _bulk_process_time_bins(
    session, time_bins_map: Dict[Tuple[datetime, datetime], str]
) -> Dict[Tuple[datetime, datetime], int]:
    """Process time bins in bulk and return mapping of bin_key to time_bin_id."""
    result_dict = {}

    if not time_bins_map:
        return result_dict

    bin_keys = list(time_bins_map.keys())
    existing_time_bins = []

    batch_size = 500
    for i in range(0, len(bin_keys), batch_size):
        batch_keys = bin_keys[i : i + batch_size]

        for key in batch_keys:
            time_bin = session.execute(
                select(TransportTimeBin).where(
                    (TransportTimeBin.start_timestamp == key[0])
                    & (TransportTimeBin.end_timestamp == key[1])
                )
            ).scalar_one_or_none()

            if time_bin:
                existing_time_bins.append(time_bin)
                result_dict[key] = time_bin.id

    time_bins_to_add = []
    for (start_timestamp, end_timestamp), cat_day in time_bins_map.items():
        if (start_timestamp, end_timestamp) not in result_dict:
            time_bins_to_add.append(
                {
                    "start_timestamp": start_timestamp,
                    "end_timestamp": end_timestamp,
                    "cat_day": cat_day,
                }
            )

    if time_bins_to_add:
        for time_bin_data in time_bins_to_add:
            time_bin = TransportTimeBin(**time_bin_data)
            session.add(time_bin)
            session.flush()
            result_dict[(time_bin.start_timestamp, time_bin.end_timestamp)] = (
                time_bin.id
            )

    return result_dict


def _bulk_process_traffic(
    session, traffic_records: List[Dict[str, Any]], bulk_size: int = 1000
) -> int:
    """Process traffic data in bulk with specified batch size and return count of records processed."""
    if not traffic_records:
        return 0

    total_processed = 0

    for i in range(0, len(traffic_records), bulk_size):
        batch = traffic_records[i : i + bulk_size]

        records_to_update = []
        records_to_insert = []

        for record in batch:
            traffic = session.execute(
                select(Traffic).where(
                    (Traffic.station_id == record["station_id"])
                    & (Traffic.time_bin_id == record["time_bin_id"])
                )
            ).scalar_one_or_none()

            if traffic:
                traffic.validations = record["validations"]
                records_to_update.append(traffic)
            else:
                records_to_insert.append(
                    Traffic(
                        station_id=record["station_id"],
                        time_bin_id=record["time_bin_id"],
                        validations=record["validations"],
                    )
                )

        if records_to_insert:
            session.add_all(records_to_insert)

        session.flush()
        total_processed += len(batch)

    return total_processed


def _create_timestamps(date_val: str, time_range_str: str) -> Tuple[datetime, datetime]:
    if isinstance(date_val, pd.Timestamp):
        date_obj = date_val.to_pydatetime()
    else:
        date_obj = datetime.strptime(date_val, "%Y-%m-%d")

    start_hour, end_hour = map(int, time_range_str.replace("H", "").split("-"))

    start_timestamp = date_obj.replace(hour=start_hour, minute=0, second=0)
    end_timestamp = date_obj.replace(hour=end_hour, minute=0, second=0)

    return start_timestamp, end_timestamp
