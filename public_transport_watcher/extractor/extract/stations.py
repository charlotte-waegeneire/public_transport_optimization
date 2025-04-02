import pandas as pd

from public_transport_watcher.extractor.insert import insert_stations_informations
from public_transport_watcher.utils import get_datalake_file


def extract_stations_informations(batch_size: int = 100):
    stations_file = get_datalake_file("geography", "stations")
    stations_file = stations_file[0]

    stations_df = pd.read_csv(stations_file, sep=";", encoding="utf-8")
    useful_columns = ["Geo Point", "id_ref_ZdC", "nom_ZdC", "mode"]
    stations_df = stations_df[useful_columns]

    stations_df[["latitude", "longitude"]] = stations_df["Geo Point"].str.split(
        ",", expand=True
    )
    stations_df = stations_df.drop(columns=["Geo Point"])

    stations_df = stations_df[stations_df["mode"] == "METRO"]
    stations_df = stations_df.drop(columns=["mode"])

    columns_mapping = {
        "id_ref_ZdC": "id",
        "nom_ZdC": "name",
    }
    stations_df = stations_df.rename(columns=columns_mapping)

    insert_stations_informations(stations_df, batch_size)
