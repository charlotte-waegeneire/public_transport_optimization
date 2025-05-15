import pandas as pd

from public_transport_watcher.logging_config import logger


def preprocess_data(df, station_id):
    station_data = df[df["station_id"] == station_id].copy()

    station_data = station_data.sort_index()

    validations_series = station_data["validations"].copy()

    hour_index = pd.DatetimeIndex(validations_series.index)
    hour_series = pd.Series(hour_index.hour, index=validations_series.index)
    dow_series = pd.Series(hour_index.weekday, index=validations_series.index)
    month_series = pd.Series(hour_index.month, index=validations_series.index)
    cat_day_series = pd.Series(station_data["cat_day"].values, index=validations_series.index)

    result_df = pd.DataFrame(
        {
            "validations": validations_series,
            "hour": hour_series,
            "day_of_week": dow_series,
            "month": month_series,
            "cat_day": cat_day_series,
        }
    )

    logger.info(f"Period covered by the data: {validations_series.index.min()} to {validations_series.index.max()}")

    return result_df
