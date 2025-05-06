from public_transport_watcher.logging_config import get_logger
import pandas as pd
import numpy as np
from sqlalchemy.orm import sessionmaker

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
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    if station_id is None:
        stations_query = """
        SELECT DISTINCT s.id, s.name
        FROM transport.station s
        JOIN transport.traffic t ON s.id = t.station_id
        LIMIT 10
        """
        stations_df = pd.read_sql(stations_query, engine)
        if not stations_df.empty:
            logger.info(f"Available stations: {stations_df.to_dict('records')}")

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
    """

    if station_id:
        query += f" WHERE t.station_id = {station_id}"

    query += " ORDER BY t.time_bin_id"

    df = pd.read_sql(query, engine)
    session.close()

    logger.info(f"Data retrieved: {len(df)} rows")

    if 'start_timestamp' in df.columns and not df.empty:
        df['datetime'] = pd.to_datetime(df['start_timestamp'])
        df.set_index('datetime', inplace=True)

    logger.debug(df.head())
    return df


def prepare_data(df, station_id=None):
    """
        Prepares the data for analysis by performing resampling,
        anomaly detection, and interpolation.

        Args:
            df (DataFrame): Raw traffic data
            station_id (int, optional): ID of the station to filter

        Returns:
            Series: Cleaned and prepared time series for analysis
        """
    if station_id is not None and 'station_id' in df.columns:
        df = df[df['station_id'] == station_id]

    timeseries = df.resample('H')['validations'].sum()

    rolling_stats = timeseries.rolling(window=24, min_periods=1)
    upper_limit = rolling_stats.mean() + 3 * rolling_stats.std().fillna(timeseries.std())
    lower_limit = rolling_stats.mean() - 3 * rolling_stats.std().fillna(timeseries.std())

    timeseries_clean = timeseries.copy()
    timeseries_clean[(timeseries > upper_limit) | (timeseries < lower_limit)] = np.nan
    timeseries_clean = timeseries_clean.interpolate(method='time').fillna(method='bfill').fillna(method='ffill')

    logger.debug(timeseries_clean.head())
    return timeseries_clean

