import pandas as pd
from typing import Dict, List, Union, Tuple
import logging

from public_transport_watcher.utils import get_datalake_file
from public_transport_watcher.extractor.insert import insert_navigo_data

logger = logging.getLogger(__name__)


def extract_navigo_validations(config: Dict, batch_size: int) -> None:
    """
    Extract and process Navigo validations for all configured time periods.

    Parameters
    ----------
    config : Dict
        Configuration dictionary with years and their corresponding time periods.
    batch_size : int
        Number of records to process at once.
    """
    for year, periods in config.items():
        _process_year_data(year, periods, batch_size)


def _process_year_data(
    year: int, periods: List[Union[str, Dict]], batch_size: int
) -> None:
    for period in periods:
        if isinstance(period, str):
            # Simple period (e.g., "s1", "s2")
            _process_period_data(year, period, batch_size)
        elif isinstance(period, dict):
            # Complex period with sub-periods (e.g., {"s2": ["3", "4"]})
            for semester, trimesters in period.items():
                for trimester in trimesters:
                    _process_period_data(year, f"{semester}/{trimester}", batch_size)


def _process_period_data(year: int, period: str, batch_size: int) -> None:
    try:
        data_category = "validations_navigo"
        files = get_datalake_file(data_category, year, period)

        if len(files) < 2:
            logger.error(f"Missing files for period {year}/{period}")
            return

        validations_file, profiles_file = _find_file_types(files)

        if not validations_file or not profiles_file:
            logger.error(
                f"Could not identify validations and profiles files for {year}/{period}"
            )
            return

        logger.info(f"Processing data for {year}/{period}")

        # Load entire profiles data into memory as it's smaller
        profiles_df = pd.read_csv(profiles_file, sep=";")
        profiles_df.columns = profiles_df.columns.str.lower()
        profiles_df = profiles_df.rename(columns={"cat_jour": "cat_day"})
        profiles_df = profiles_df[profiles_df["trnc_horr_60"] != "ND"]

        # Process validations data in batches to save memory
        chunks_processed = 0
        total_records = 0

        for validations_chunk in pd.read_csv(
            validations_file, sep=";", chunksize=batch_size
        ):
            chunks_processed += 1
            records_in_chunk = len(validations_chunk)
            total_records += records_in_chunk

            logger.info(
                f"Processing chunk {chunks_processed} with {records_in_chunk} records"
            )

            hourly_validations = _compute_hourly_validations(
                validations_chunk, profiles_df
            )

            if not hourly_validations.empty:
                # Insert the resulting hourly validations in one go - no need for batching here
                insert_navigo_data(hourly_validations)

            logger.info(
                f"Chunk {chunks_processed} processed, {total_records} total records so far"
            )

        logger.info(
            f"Completed processing for {year}/{period} - {total_records} total records in {chunks_processed} chunks"
        )

    except Exception as e:
        logger.error(f"Error processing {year}/{period}: {str(e)}")


def _find_file_types(files: List[str]) -> Tuple[str, str]:
    validations_file = None
    profiles_file = None

    for file in files:
        if "validations" in file.lower():
            validations_file = file
        elif "profils" in file.lower() or "profiles" in file.lower():
            profiles_file = file

    return validations_file, profiles_file


def _compute_hourly_validations(
    validations_df: pd.DataFrame, profiles_df: pd.DataFrame
) -> pd.DataFrame:
    validations_df.columns = validations_df.columns.str.lower()

    # Handle "5 or less" validations
    if "nb_vald" in validations_df.columns:
        validations_df["nb_vald"] = pd.to_numeric(
            validations_df["nb_vald"], errors="coerce"
        )
        validations_df["nb_vald"] = validations_df["nb_vald"].fillna(3)

    merge_keys = [
        "code_stif_arret",
        "code_stif_res",
        "code_stif_trns",
        "libelle_arret",
        "ida",
    ]
    group_cols = merge_keys + ["jour"]

    if "jour" in validations_df.columns:
        validations_df["jour"] = pd.to_datetime(validations_df["jour"])
        validations_df["cat_day"] = validations_df.apply(_determine_day_type, axis=1)
        group_cols.append("cat_day")

    validations_aggr = validations_df.groupby(group_cols, as_index=False).agg(
        nb_vald_total=("nb_vald", "sum")
    )

    validations_aggr.rename(columns={"nb_vald_total": "nb_vald"}, inplace=True)
    merge_keys_full = merge_keys + ["cat_day"]

    merged_df = pd.merge(validations_aggr, profiles_df, on=merge_keys_full, how="inner")

    merged_df["validations_horaires"] = (
        merged_df["nb_vald"] * merged_df["pourc_validations"] / 100
    )

    validation_cols = list(validations_aggr.columns)
    cols_to_add = ["trnc_horr_60", "validations_horaires", "pourc_validations"]

    result_df = merged_df[validation_cols + cols_to_add].copy()
    result_df.rename(columns={"trnc_horr_60": "tranche_horaire"}, inplace=True)

    return result_df


def _determine_day_type(row: pd.Series) -> str:
    day_of_week = row["jour"].dayofweek
    day_of_week_mapping = {
        5: "SAHV",  # Saturday
        6: "DIJFP",  # Sunday
    }
    # Default to JOHV for weekdays
    # TODO holidays and other special days
    return day_of_week_mapping.get(day_of_week, "JOHV")
