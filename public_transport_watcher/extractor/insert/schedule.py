from logging import getLogger

import pandas as pd
from sqlalchemy.orm import sessionmaker

from public_transport_watcher.db.models import Schedule, Transport, TransportStation
from public_transport_watcher.utils import get_engine

logger = getLogger()


def insert_schedule_data(df: pd.DataFrame) -> None:
    """
    Insert schedule data into the database.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing schedule data to be inserted.
    """
    logger.info("Inserting schedule data into the database...")

    if df.empty:
        logger.warning("Empty schedule DataFrame. Nothing to insert.")
        return

    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        existing_station_ids = {id for (id,) in session.query(TransportStation.id).distinct().all()}
        logger.info(f"Found {len(existing_station_ids)} existing station IDs.")

        initial_len = len(df)
        df = df[df["stop_id"].isin(existing_station_ids)]
        filtered_len = len(df)
        excluded_rows = initial_len - filtered_len
        if excluded_rows > 0:
            logger.info(f"Filtered schedule DataFrame: {excluded_rows} rows excluded due to missing station_id.")

        existing_transport_ids = {id for (id,) in session.query(Transport.id).distinct().all()}

        before_len = len(df)
        df = df[df["line_numeric_id"].isin(existing_transport_ids)]
        excluded_rows = before_len - len(df)
        if excluded_rows > 0:
            logger.info(f"Filtered schedule DataFrame: {excluded_rows} rows excluded due to missing transport_id.")

        inserted = 0
        for _, row in df.iterrows():
            if pd.isnull(row["arrival_timestamp"]):
                continue

            # Validate if next_station_id exists in the database
            if pd.notnull(row["next_station_id"]) and row["next_station_id"] not in existing_station_ids:
                logger.warning(f"Skipping schedule with invalid next_station_id {row['next_station_id']}.")
                continue

            try:
                schedule = Schedule(
                    timestamp=row["arrival_timestamp"],
                    station_id=int(row["stop_id"]),
                    next_station_id=int(row["next_station_id"]) if pd.notnull(row["next_station_id"]) else None,
                    transport_id=int(row["line_numeric_id"]),
                )
                session.add(schedule)
                inserted += 1
            except Exception as row_error:
                logger.error(f"Error inserting schedule row: {row_error}")
                continue

        session.commit()
        logger.info(f"{inserted} schedule(s) inserted into `schedule` table.")

    except Exception as e:
        session.rollback()
        logger.error(f"Error during schedule insertion: {e}")
        raise

    finally:
        session.close()
