import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_engine

logger = get_logger()


def insert_stations_informations(stations: pd.DataFrame, batch_size: int = 100) -> None:
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
    stations["id"] = stations["id"].astype(int)
    stations["name"] = stations["name"].astype(str)
    stations["latitude"] = stations["latitude"].astype(float)
    stations["longitude"] = stations["longitude"].astype(float)

    engine = get_engine()

    try:
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

            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                connection.execute(text(insert_stmt), batch)

            connection.commit()

        print(
            f"Successfully inserted/updated {len(stations)} stations in the database."
        )

    except SQLAlchemyError as e:
        print(f"Error inserting/updating stations data: {e}")
        raise
