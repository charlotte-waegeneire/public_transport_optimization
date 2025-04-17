from public_transport_watcher.extractor.extract.traffic import _extract_lines_data
from typing import Tuple, List, Dict, Any
from datetime import datetime

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert

from public_transport_watcher.db.models.transport import (
    TransportStation,
    TransportTimeBin,
    Traffic,
)
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
        df_transport = df_transport[["ID_Line", "TransportMode"]].dropna()
        df_transport["TransportMode"] = (
            df_transport["TransportMode"]
            .str.strip()
            .str.lower()
        )
        df_transport["numeric_id"] = df_transport["ID_Line"].str.lstrip("C").astype(int)
        return df_transport
    except Exception as e:
        logger.error(f"Failed to extract transport data: {e}")
        return pd.DataFrame()
