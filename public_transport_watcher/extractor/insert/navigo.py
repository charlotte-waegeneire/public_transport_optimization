import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
import logging
from typing import Tuple
from datetime import datetime

from public_transport_watcher.utils import get_engine
from public_transport_watcher.db.models.transport import (
    TransportStation,
    TransportTimeBin,
    Traffic,
)

logger = logging.getLogger(__name__)


def insert_navigo_data(df: pd.DataFrame) -> None:
    """
    Insert Navigo validations data into the database.

    Parameters
    ----------
    df : DataFrame
        Navigo validations data.
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Counters to track operations
        stations_added = 0
        time_bins_added = 0
        traffic_records_added = 0

        # Process row by row
        for _, row in df.iterrows():
            try:
                # Process station
                station_id = int(row["code_stif_arret"])
                station_name = row["libelle_arret"]

                station = _get_or_create_station(session, station_id, station_name)
                if station.is_new:
                    stations_added += 1

                # Process time_bin
                start_timestamp, end_timestamp = _create_timestamps(
                    row["jour"], row["tranche_horaire"]
                )

                time_bin = _get_or_create_time_bin(
                    session, start_timestamp, end_timestamp, row["cat_day"]
                )
                if time_bin.is_new:
                    time_bins_added += 1

                # Process traffic
                traffic = _get_or_create_traffic(
                    session, station_id, time_bin.id, row["validations_horaires"]
                )
                if traffic.is_new:
                    traffic_records_added += 1

            except Exception as row_error:
                logger.error(f"Error processing row: {row_error}")
                logger.debug(f"Row data: {row}")
                continue

        # Commit all changes at once
        session.commit()

        logger.info(
            f"Insertion completed: {stations_added} stations, {time_bins_added} time bins, {traffic_records_added} traffic records"
        )

    except Exception as e:
        session.rollback()
        logger.error(f"Error inserting data: {str(e)}")
        raise
    finally:
        session.close()


def _create_timestamps(date_val: str, time_range_str: str) -> Tuple[datetime, datetime]:
    if isinstance(date_val, pd.Timestamp):
        date_obj = date_val.to_pydatetime()
    else:
        date_obj = datetime.strptime(date_val, "%Y-%m-%d")

    start_hour, end_hour = map(int, time_range_str.replace("H", "").split("-"))

    start_timestamp = date_obj.replace(hour=start_hour, minute=0, second=0)
    end_timestamp = date_obj.replace(hour=end_hour, minute=0, second=0)

    return start_timestamp, end_timestamp


def _get_or_create_station(session, station_id: int, station_name: str):
    station = session.execute(
        select(TransportStation).where(TransportStation.id == station_id)
    ).scalar_one_or_none()

    is_new = False
    if not station:
        station = TransportStation(
            id=station_id,
            name=station_name,
        )
        session.add(station)
        is_new = True

    station.is_new = is_new
    return station


def _get_or_create_time_bin(
    session, start_timestamp: datetime, end_timestamp: datetime, cat_day: str
):
    time_bin = session.execute(
        select(TransportTimeBin).where(
            (TransportTimeBin.start_timestamp == start_timestamp)
            & (TransportTimeBin.end_timestamp == end_timestamp)
        )
    ).scalar_one_or_none()

    is_new = False
    if not time_bin:
        time_bin = TransportTimeBin(
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            cat_day=cat_day,
        )
        session.add(time_bin)
        session.flush()
        is_new = True

    time_bin.is_new = is_new
    return time_bin


def _get_or_create_traffic(
    session, station_id: int, time_bin_id: int, validations: float
):
    traffic = session.execute(
        select(Traffic).where(
            (Traffic.station_id == station_id) & (Traffic.time_bin_id == time_bin_id)
        )
    ).scalar_one_or_none()

    validations_value = int(float(validations))

    is_new = False
    if not traffic:
        traffic = Traffic(
            station_id=station_id,
            time_bin_id=time_bin_id,
            validations=validations_value,
        )
        session.add(traffic)
        is_new = True
    else:
        traffic.validations = validations_value

    traffic.is_new = is_new
    return traffic
