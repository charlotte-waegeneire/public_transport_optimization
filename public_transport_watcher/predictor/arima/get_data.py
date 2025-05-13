import pandas as pd
from sqlalchemy.orm import sessionmaker

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_engine

logger = get_logger()


def get_data_from_db(station_id=None):
    """
    Retrieves traffic data from the database.

    Args:
        station_id (int, optional): ID of the station to analyze. If None,
                                    retrieves data for all stations.

    Returns:
        DataFrame: Traffic data with timestamps
    """
    if station_id is None:
        logger.error("Station ID is required.")
        return None

    if not isinstance(station_id, int):
        logger.error("Station ID must be an integer.")
        return None

    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    query = """
    SELECT 
        t.station_id,
        s.name as station_name,
        t.time_bin_id,
        tb.cat_day,
        tb.start_timestamp,
        tb.end_timestamp,
        t.validations
    FROM 
        transport.traffic t
    JOIN 
        transport.station s ON t.station_id = s.id
    JOIN 
        transport.time_bin tb ON t.time_bin_id = tb.id
    WHERE
        t.station_id = %(station_id)s
    ORDER BY t.time_bin_id
    """

    params = {"station_id": station_id}

    # Use SQLAlchemy prepared parameters to avoid SQL injection
    df = pd.read_sql(query, engine, params=params)
    session.close()

    logger.info(f"Data retrieved: {len(df)} rows")

    if "start_timestamp" in df.columns and not df.empty:
        df["datetime"] = pd.to_datetime(df["start_timestamp"])
        df.set_index("datetime", inplace=True)

    return df
