import pandas as pd
from sqlalchemy.orm import sessionmaker

from public_transport_watcher.db.models import Schedule, Transport, TransportStation
from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_engine

logger = get_logger()


def insert_schedule_informations(df: pd.DataFrame, config: dict) -> None:
    """
    Insert schedule data into the database.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing schedule data to be inserted.
    """
    logger.info("Inserting schedule data into the database...")
    chunk_size = config.get("batch_size", 5000)

    if df.empty:
        logger.warning("Empty schedule DataFrame. Nothing to insert.")
        return

    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        existing_station_ids = {id for (id,) in session.query(TransportStation.id).distinct().all()}
        df = df[df["stop_id"].isin(existing_station_ids)]

        existing_transport_ids = {id for (id,) in session.query(Transport.id).distinct().all()}
        df = df[df["line_numeric_id"].isin(existing_transport_ids)]

        logger.debug(f"Preparing to insert {len(df)} rows")

        inserted = 0
        skipped_timestamp = 0
        skipped_next_station = 0
        skipped_errors = 0

        total_chunks = (len(df) + chunk_size - 1) // chunk_size
        logger.info(f"Processing {total_chunks} chunks of {chunk_size} rows each")

        for chunk_idx, chunk_start in enumerate(range(0, len(df), chunk_size)):
            chunk_end = min(chunk_start + chunk_size, len(df))
            chunk = df.iloc[chunk_start:chunk_end]
            chunk_inserted = 0

            for _, row in chunk.iterrows():
                if pd.isnull(row["arrival_timestamp"]):
                    skipped_timestamp += 1
                    continue

                if pd.notnull(row["next_station_id"]) and row["next_station_id"] not in existing_station_ids:
                    skipped_next_station += 1
                    continue

                try:
                    schedule = Schedule(
                        timestamp=row["arrival_timestamp"],
                        station_id=int(row["stop_id"]),
                        next_station_id=int(row["next_station_id"]) if pd.notnull(row["next_station_id"]) else None,
                        transport_id=int(row["line_numeric_id"]),
                        journey_id=str(row["journey_id"]) if pd.notnull(row["journey_id"]) else None,
                    )
                    session.add(schedule)
                    inserted += 1
                    chunk_inserted += 1
                except Exception as row_error:
                    logger.error(f"Error inserting schedule row: {row_error}")
                    skipped_errors += 1
                    continue

            session.commit()
            logger.info(f"Chunk {chunk_idx + 1}/{total_chunks} complete: inserted {chunk_inserted} rows")

        logger.info(f"Insertion complete: {inserted} schedules inserted")
        logger.debug(
            f"Skipped rows - null timestamp: {skipped_timestamp}, invalid next_station: {skipped_next_station}, errors: {skipped_errors}"
        )

    except Exception as e:
        session.rollback()
        logger.error(f"Error during schedule insertion: {e}")
        raise

    finally:
        session.close()
