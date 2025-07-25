import datetime

import pandas as pd


def calculate_hourly_profile(data_df: pd.DataFrame, current_time: datetime) -> pd.Series:
    """
    Calculate average hourly profile for a given day and month.

    Parameters
    ----------
    data_df : pd.DataFrame
        Preprocessed data
    current_time : datetime
        Current time

    Returns
    -------
    pd.Series
        Average validations by hour
    """
    current_month = current_time.month
    current_day_of_week = current_time.weekday()

    similar_hours = data_df[(data_df["month"] == current_month) & (data_df["day_of_week"] == current_day_of_week)]

    if not similar_hours.empty:
        hourly_avg = similar_hours.groupby("hour")["validations"].mean()
    else:
        hourly_avg = pd.Series(dtype=float)

    return hourly_avg
