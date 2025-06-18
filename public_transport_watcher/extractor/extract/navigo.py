from typing import Dict, List, Tuple, Union

from holidays import France
import pandas as pd

from public_transport_watcher.extractor.configuration import COLUMN_MAPPING
from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_datalake_file

logger = get_logger()
_HOLIDAYS = France(years=[2023, 2024]).keys()

_COLUMN_MAPPING = COLUMN_MAPPING["navigo"]


def extract_navigo_validations_informations(config: Dict) -> pd.DataFrame:
    """
    Extract and process Navigo validations for all configured time periods.

    Parameters
    ----------
    config : Dict
        Configuration dictionary with years and their corresponding time periods.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the processed Navigo validations data.
    """
    logger.info("Extracting Navigo validations")

    files_config = config["files"]
    batch_size = config["batch_size"]

    if not files_config:
        logger.error("No files configuration provided for Navigo validations extraction.")
        return pd.DataFrame()

    all_validations = []
    failures = []
    for year, periods in files_config.items():
        try:
            year_validations = _process_year_data(year, periods, batch_size)
            if not year_validations.empty:
                all_validations.append(year_validations)
        except Exception as e:
            logger.error(f"Failed to process year {year}: {str(e)}")
            failures.append(year)

    if failures:
        logger.warning(f"Failed to process data for years: {failures}")

    if not all_validations:
        logger.warning("No validations data was extracted")
        return pd.DataFrame()

    final_df = pd.concat(all_validations, ignore_index=True)
    logger.info(f"Successfully extracted {len(final_df)} validation records")
    return final_df


def _process_year_data(year: int, periods: List[Union[str, Dict]], batch_size: int) -> pd.DataFrame:
    all_period_validations = []
    for period in periods:
        if isinstance(period, str):
            # Simple period (e.g., "s1", "s2")
            period_df = _process_period_data(year, period, batch_size)
            if not period_df.empty:
                all_period_validations.append(period_df)
        elif isinstance(period, dict):
            # Complex period with sub-periods (e.g., {"s2": ["3", "4"]})
            for semester, trimesters in period.items():
                for trimester in trimesters:
                    period_df = _process_period_data(year, f"{semester}/{trimester}", batch_size)
                    if not period_df.empty:
                        all_period_validations.append(period_df)

    if not all_period_validations:
        return pd.DataFrame()

    return pd.concat(all_period_validations, ignore_index=True)


def _process_period_data(year: int, period: str, batch_size: int) -> pd.DataFrame:
    try:
        data_category = "validations_navigo"
        files = get_datalake_file(data_category, year, period)

        if len(files) < 2:
            logger.error(f"Missing files for period {year}/{period}")
            return pd.DataFrame()

        validations_file, profiles_file = _find_file_types(files)

        if not validations_file or not profiles_file:
            logger.error(f"Could not identify validations and profiles files for {year}/{period}")
            return pd.DataFrame()

        logger.info(f"Processing data for {year}/{period}")

        try:
            profiles_df = pd.read_csv(profiles_file, sep=";", parse_dates=False, encoding="latin1")
        except Exception as e:
            logger.error(f"Error loading profiles file: {str(e)}")
            return pd.DataFrame()

        profiles_df.columns = _COLUMN_MAPPING["profils"]
        profiles_df = profiles_df.rename(columns={"cat_jour": "cat_day"})
        profiles_df = profiles_df[profiles_df["trnc_horr_60"] != "ND"]

        # Process validations data in batches to save memory
        chunks_processed = 0
        total_records = 0
        all_chunks = []

        for validations_chunk in pd.read_csv(
            validations_file, sep=";", encoding="latin1", chunksize=batch_size, parse_dates=False
        ):
            validations_chunk.columns = _COLUMN_MAPPING["validations"]
            chunks_processed += 1
            records_in_chunk = len(validations_chunk)
            total_records += records_in_chunk

            logger.info(f"Processing chunk {chunks_processed} with {records_in_chunk} records")

            hourly_validations = _compute_hourly_validations(validations_chunk, profiles_df)
            if not hourly_validations.empty:
                all_chunks.append(hourly_validations)

            logger.info(f"Chunk {chunks_processed} processed, {total_records} total records so far")

        if not all_chunks:
            return pd.DataFrame()

        final_df = pd.concat(all_chunks, ignore_index=True)
        logger.info(
            f"Completed processing for {year}/{period} - {total_records} total records in {chunks_processed} chunks"
        )
        return final_df

    except Exception as e:
        logger.error(f"Error processing {year}/{period}: {str(e)}")
        return pd.DataFrame()


def _find_file_types(files: List[str]) -> Tuple[str, str]:
    validations_file = None
    profils_file = None

    for file in files:
        if "validations.csv" in file.lower():
            validations_file = file
            continue
        if "profils.csv" in file.lower() or "profils" in file.lower():
            profils_file = file
            continue

    return validations_file, profils_file


def _compute_hourly_validations(validations_df: pd.DataFrame, profiles_df: pd.DataFrame) -> pd.DataFrame:
    # Handle "5 or less" validations
    if "nb_vald" in validations_df.columns:
        validations_df["nb_vald"] = pd.to_numeric(validations_df["nb_vald"], errors="coerce")
        validations_df["nb_vald"] = validations_df["nb_vald"].fillna(3)

    validations_df = validations_df[validations_df["code_stif_arret"] != "ND"]
    validations_df = validations_df[validations_df["code_stif_res"] != "ND"]
    validations_df = validations_df[validations_df["code_stif_trns"] != "ND"]

    merge_keys = [
        "code_stif_arret",
        "code_stif_res",
        "code_stif_trns",
        "libelle_arret",
        "ida",
    ]
    group_cols = merge_keys + ["jour"]

    if "jour" in validations_df.columns:
        try:
            validations_df["jour"] = pd.to_datetime(validations_df["jour"], format="%d/%m/%Y", errors="raise")
        except ValueError:
            try:
                validations_df["jour"] = pd.to_datetime(validations_df["jour"], format="%Y-%m-%d", errors="raise")
            except ValueError:
                validations_df["jour"] = pd.to_datetime(
                    validations_df["jour"],
                    format="mixed",
                    dayfirst=True,
                    errors="coerce",
                )
        validations_df["cat_day"] = validations_df.apply(_determine_day_type, axis=1)
        group_cols.append("cat_day")

    validations_aggr = validations_df.groupby(group_cols, as_index=False).agg(nb_vald_total=("nb_vald", "sum"))

    validations_aggr.rename(columns={"nb_vald_total": "nb_vald"}, inplace=True)
    merge_keys_full = merge_keys + ["cat_day"]

    merged_df = pd.merge(validations_aggr, profiles_df, on=merge_keys_full, how="inner")

    merged_df["validations_horaires"] = merged_df["nb_vald"] * merged_df["pourc_validations"] / 100

    validation_cols = list(validations_aggr.columns)
    cols_to_add = ["trnc_horr_60", "validations_horaires", "pourc_validations"]

    result_df = merged_df[validation_cols + cols_to_add].copy()
    result_df.rename(columns={"trnc_horr_60": "tranche_horaire"}, inplace=True)

    first_labels = result_df.drop_duplicates(subset=["ida", "jour", "tranche_horaire"], keep="first")[
        ["ida", "jour", "tranche_horaire", "libelle_arret"]
    ]

    result_df = result_df.drop(columns=["libelle_arret"])
    result_df = pd.merge(result_df, first_labels, on=["ida", "jour", "tranche_horaire"])

    result_df = (
        result_df.groupby(["ida", "libelle_arret", "jour", "cat_day", "tranche_horaire"])["validations_horaires"]
        .sum()
        .reset_index()
    )

    return result_df


def _determine_day_type(row: pd.Series) -> str:
    jour = row["jour"]
    day_of_week = jour.dayofweek

    if jour in _HOLIDAYS or day_of_week == 6:
        return "DIJFP"

    return "SAHV" if day_of_week == 5 else "JOHV"
