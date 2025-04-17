import pandas as pd

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_datalake_file

logger = get_logger()

def _extract_lines_data() -> pd.DataFrame:
    """
    Loads lines data from the CSV file.
    """
    try:
        file_path = next(
            f
            for f in get_datalake_file("schedule", 2025, "")
            if "referentiel-des-lignes.csv" in f
        )
        return pd.read_csv(file_path, sep=";")
    except (StopIteration, FileNotFoundError) as e:
        logger.error(f"Failed to load row data : {e}")
        return pd.DataFrame()

# def _extract_schedule_data() -> pd.DataFrame:
#     """
#     Loads lines data from the CSV file.
#     """
#     try:
#         file_path = next(
#             f
#             for f in get_datalake_file("schedule", 2025, "files")
#             if "schedule.csv" in f
#         )
#         return pd.read_csv(file_path, sep=";")
#     except (StopIteration, FileNotFoundError) as e:
#         logger.error(f"Failed to load row data : {e}")
#         return pd.DataFrame()
