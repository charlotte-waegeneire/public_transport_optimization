import pandas as pd

from public_transport_watcher.extractor.extract.traffic import _extract_lines_data
from public_transport_watcher.logging_config import get_logger

logger = get_logger()


def extract_transport_data() -> pd.DataFrame:
    """
    Extracts and cleans transport line data.
    Loads the lines data from a CSV file, normalizes transport modes,
    and extracts a numeric ID from the 'ID_Line' column.
    """
    try:
        df_transport = _extract_lines_data()
        logger.info(f"Raw transport data extracted: {len(df_transport)} rows")

        # Log samples of raw IDs
        if not df_transport.empty:
            logger.info(
                f"Sample raw ID_Line values: {df_transport['ID_Line'].sample(min(5, len(df_transport))).tolist()}"
            )

        df_transport = df_transport[["ID_Line", "TransportMode"]].dropna()
        logger.info(f"After dropna: {len(df_transport)} rows")

        df_transport["TransportMode"] = df_transport["TransportMode"].str.strip().str.lower()

        # Original extraction method
        df_transport["numeric_id"] = df_transport["ID_Line"].str.lstrip("C").astype(int)

        logger.info(f"Unique numeric_id count: {df_transport['numeric_id'].nunique()}")
        logger.info(
            f"Sample numeric_id values: {df_transport['numeric_id'].sample(min(10, len(df_transport))).tolist()}"
        )

        return df_transport
    except Exception as e:
        logger.error(f"Failed to extract transport data: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return pd.DataFrame()
