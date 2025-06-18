import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_engine

logger = get_logger()


def insert_stations(stations: pd.DataFrame, batch_size: int = 1000) -> None:
    """
    Insert or update stations information into the database.

    Parameters
    ----------
    stations
        DataFrame containing stations information with columns:
        id, name, latitude, longitude
    batch_size
        Number of records to insert in each batch
    """
    if stations.empty:
        logger.warning("No station data to insert")
        return

    logger.info(f"Preparing to insert/update {len(stations)} stations")

    try:
        stations["id"] = stations["id"].astype(int)
        stations["name"] = stations["name"].astype(str)
        stations["latitude"] = stations["latitude"].astype(float)
        stations["longitude"] = stations["longitude"].astype(float)

        engine = get_engine()
        logger.debug("Database connection established")

        with engine.connect() as connection:
            insert_stmt = """
                INSERT INTO transport.station (id, name, latitude, longitude)
                VALUES (:id, :name, :latitude, :longitude)
                ON CONFLICT (id) DO UPDATE 
                SET name = EXCLUDED.name,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude
            """

            records = stations.to_dict(orient="records")
            total_batches = (len(records) + batch_size - 1) // batch_size

            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                current_batch = (i // batch_size) + 1
                logger.debug(f"Processing batch {current_batch}/{total_batches} ({len(batch)} records)")
                connection.execute(text(insert_stmt), batch)

            connection.commit()
            logger.info(f"Successfully inserted/updated {len(stations)} stations in the database")

    except SQLAlchemyError as e:
        logger.error(f"Database error inserting/updating stations: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during station insertion: {e}")
        raise
