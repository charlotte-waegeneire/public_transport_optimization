from typing import Dict, List, Optional

import pandas as pd

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_datalake_file

logger = get_logger()

column_names = [
    "start_datetime",
    "end_datetime",
    "organism",
    "zas_code",
    "zas",
    "site_code",
    "site",
    "implementation",
    "pollutant",
    "influence",
    "discriminant",
    "required",
    "eval_type",
    "mesure_procedure",
    "value_type",
    "value",
    "raw_value",
    "unit",
    "entry_rate",
    "time_covering",
    "data_covering",
    "quality_code",
    "validity",
]


def extract_air_quality_data(
    pollutants: Optional[List[str]] = None,
    limits: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """
    Process air quality data from CSV file.

    Parameters
    ----------
    pollutants
        List of pollutants to keep.
    limits
        Dictionary of pollutant limits.

    Returns
    -------
        Processed DataFrame with pollutant values and their limits.
    """
    if pollutants is None:
        logger.error("No pollutants specified")
        return pd.DataFrame()

    if limits is None:
        logger.error("No limits specified")

    lcsqa_file = get_datalake_file("lcsqa", "latest")[0]

    air_quality_df = pd.read_csv(lcsqa_file, sep=";", encoding="latin1")
    air_quality_df.columns = column_names

    air_quality_df = air_quality_df[air_quality_df["organism"] == "AIRPARIF"]

    air_quality_df = air_quality_df[air_quality_df["site"].str.startswith("PARIS")]

    air_quality_df["start_datetime"] = pd.to_datetime(air_quality_df["start_datetime"])
    air_quality_df["end_datetime"] = pd.to_datetime(air_quality_df["end_datetime"])

    last_time_interval = air_quality_df["start_datetime"].max()
    air_quality_df = air_quality_df[air_quality_df["start_datetime"] == last_time_interval]

    useless_cols = [
        "organism",
        "zas",
        "influence",
        "discriminant",
        "required",
        "eval_type",
        "mesure_procedure",
        "value",
        "entry_rate",
        "time_covering",
        "data_covering",
        "implementation",
    ]
    air_quality_df = air_quality_df.drop(columns=useless_cols)

    air_quality_df = air_quality_df[air_quality_df["validity"] == 1]

    air_quality_df = air_quality_df.groupby("pollutant").agg({"raw_value": "mean"}).reset_index()
    air_quality_df["value"] = air_quality_df["raw_value"].round().astype(int)
    air_quality_df = air_quality_df.drop("raw_value", axis=1)

    air_quality_df = air_quality_df[air_quality_df["pollutant"].isin(pollutants)]

    air_quality_df["limit"] = air_quality_df["pollutant"].map(limits)
    air_quality_df["limit"] = air_quality_df["limit"].astype(int)

    air_quality_df["ratio"] = air_quality_df["value"] / air_quality_df["limit"]
    air_quality_df["ratio"] = air_quality_df["ratio"].round(2)

    return air_quality_df
