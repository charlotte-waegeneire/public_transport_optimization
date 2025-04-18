import pandas as pd

from public_transport_watcher.extractor.extract.traffic import _extract_lines_data
from public_transport_watcher.logging_config import get_logger

logger = get_logger()


def extract_categ_data() -> pd.DataFrame:
    """
    Extracts transport modes from the lines data.
    Loads the lines data from a CSV file, filters relevant columns,
    and returns a DataFrame with unique transport modes.
    """
    try:
        df_transport_type = _extract_lines_data()
        df_transport_type = df_transport_type[["ID_Line", "TransportMode"]]
        df_transport_type.loc[:, "TransportMode"] = (
            df_transport_type["TransportMode"].str.strip().str.lower()
        )
        return df_transport_type.dropna(subset=["TransportMode"]).drop_duplicates(
            subset=["TransportMode"]
        )
    except Exception as e:
        logger.error(f"Failed to extract transport categories: {e}")
        return pd.DataFrame()
