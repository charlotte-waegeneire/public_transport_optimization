import pandas as pd

from public_transport_watcher.extractor.insert import insert_stations_informations
from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_datalake_file

logger = get_logger()


def extract_stations_informations(batch_size: int = 100):
    """
    Extract and process metro station information from a CSV file.

    Parameters
    ----------
    batch_size : int, optional
        Number of records to process in each batch, by default 100
    """
    logger.info("Starting metro stations information extraction")

    try:
        stations_file = get_datalake_file("geography", "stations")
        if not stations_file:
            logger.error("No station files found in datalake")
            return

        stations_file = stations_file[0]
        logger.info(f"Processing stations from file: {stations_file}")

        stations_df = pd.read_csv(stations_file, sep=";", encoding="utf-8")
        initial_count = len(stations_df)
        logger.info(f"Loaded {initial_count} station records")

        useful_columns = [
            "Geo Point",
            "id_ref_ZdC",
            "nom_ZdC",
        ]
        stations_df = stations_df[useful_columns]

        stations_df[["latitude", "longitude"]] = stations_df["Geo Point"].str.split(",", expand=True)
        stations_df = stations_df.drop(columns=["Geo Point"])

        columns_mapping = {
            "id_ref_ZdC": "id",
            "nom_ZdC": "name",
        }
        stations_df = stations_df.rename(columns=columns_mapping)
        stations_df = stations_df.drop_duplicates(subset=["id"])
        stations_df["name"] = stations_df["name"].str.upper()

        logger.info(f"Inserting {len(stations_df)} metro stations to database")
        insert_stations_informations(stations_df, batch_size)
        logger.info("Metro stations information extraction completed successfully")

    except Exception as e:
        logger.error(f"Error processing metro stations: {str(e)}")
