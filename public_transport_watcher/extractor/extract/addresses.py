import pandas as pd

from public_transport_watcher.extractor.insert import insert_addresses_informations
from public_transport_watcher.logging_config import get_logger

logger = get_logger()


def extract_addresses_informations(batch_size: int = 1000) -> None:
    """
    Extract and process addresses information from a CSV file.

    Parameters
    ----------
        batch_size: Number of rows to process at a time (not used yet)

    Returns
    -------
        Processed DataFrame with clean address information
    """
    logger.info("Starting address information extraction")

    from public_transport_watcher.utils import get_datalake_file

    addresses_file = get_datalake_file("geography", "addresses")
    if not addresses_file:
        logger.error("No address file found in datalake")
        return

    addresses_file = addresses_file[0]
    logger.info(f"Processing addresses from file: {addresses_file}")

    try:
        addresses_df = pd.read_csv(addresses_file, sep=";", encoding="utf-8")
        initial_count = len(addresses_df)
        logger.info(f"Loaded {initial_count} address records")

        addresses_df[["latitude", "longitude"]] = addresses_df["Geometry X Y"].str.split(",", expand=True)

        useful_columns = [
            "N_SQ_AD",  # id informatique
            "N_VOIE",  # numéro de voie
            "L_ADR",  # adresse complète
            "C_SUF1",  # suffixe de voie
            "C_SUF2",  # suffixe de voie
            "C_SUF3",  # code de voie
            "C_AR",  # arrondissement parisien
            "latitude",
            "longitude",
        ]
        addresses_df = addresses_df[useful_columns]
        addresses_df = addresses_df.dropna(subset=["N_SQ_AD", "N_VOIE", "L_ADR", "C_AR"])

        clean_count = len(addresses_df)
        if initial_count > clean_count:
            logger.info(f"Removed {initial_count - clean_count} records with missing data")

        mapping_types = [int, int, str, str, str, str, int, float, float]
        mapping_types = dict(zip(useful_columns, mapping_types))
        addresses_df = addresses_df.astype(mapping_types)

        logger.info("Extracting street names and building street numbers")
        addresses_df["street_name"] = addresses_df.apply(_extract_street_name, axis=1)
        addresses_df["number"] = addresses_df.apply(_build_street_number, axis=1)

        addresses_df = addresses_df.drop(columns=["N_SQ_AD", "N_VOIE", "C_SUF1", "C_SUF2", "C_SUF3", "L_ADR"])

        logger.info(f"Inserting {len(addresses_df)} processed address records to database")
        insert_addresses_informations(addresses_df, batch_size)
        logger.info("Address information extraction completed successfully")

    except Exception as e:
        logger.error(f"Error processing addresses: {str(e)}")


def _extract_street_name(row: pd.Series) -> str:
    street_name = row["L_ADR"]
    street_name = (
        street_name.replace(str(row["N_VOIE"]), "")
        .replace(str(row["C_SUF1"]), "")
        .replace(str(row["C_SUF2"]), "")
        .replace(str(row["C_SUF3"]), "")
    )

    return street_name.strip()


def _build_street_number(row: pd.Series) -> str:
    number = str(row["N_VOIE"])
    suffixes = [row["C_SUF1"], row["C_SUF2"], row["C_SUF3"]]
    suffixes = [suffix for suffix in suffixes if suffix not in ["nan", ""]]

    if len(suffixes) > 0:
        number += " " + " ".join(suffixes)

    return number.strip()
