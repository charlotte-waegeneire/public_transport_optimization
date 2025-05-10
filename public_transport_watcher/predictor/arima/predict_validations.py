import calendar
from datetime import datetime, timedelta
import pandas as pd

from public_transport_watcher.logging_config import get_logger
import numpy as np
from statsmodels.tsa.arima.model import ARIMA

from public_transport_watcher.predictor.arima.preprocess_data import preprocess_data

logger = get_logger()


def predict_validations(df, station_id):
    data_df = preprocess_data(df, station_id)

    current_time = datetime.now()
    logger.info(f"Current date and time: {current_time}")

    current_month = current_time.month
    current_day_of_week = current_time.weekday()
    current_hour = current_time.hour

    logger.info(f"Current month: {calendar.month_name[current_month]}")
    logger.info(f"Day of the week: {calendar.day_name[current_day_of_week]}")
    logger.info(f"Hour: {current_hour}h")

    similar_hours_1 = data_df[(data_df["month"] == current_month) & (data_df["day_of_week"] == current_day_of_week)]

    similar_hours_2 = data_df[data_df["month"] == current_month]

    similar_hours_3 = data_df[data_df["day_of_week"] == current_day_of_week]

    common_cat_day = similar_hours_1["cat_day"].mode().iloc[0] if not similar_hours_1.empty else None

    if common_cat_day:
        logger.info(
            f"Most frequent day category for {calendar.day_name[current_day_of_week]} in {calendar.month_name[current_month]}: {common_cat_day}"
        )
        similar_hours_4 = data_df[data_df["cat_day"] == common_cat_day]
    else:
        similar_hours_4 = pd.DataFrame()

    hourly_avg_1 = similar_hours_1.groupby("hour")["validations"].mean() if not similar_hours_1.empty else None
    hourly_avg_2 = similar_hours_2.groupby("hour")["validations"].mean() if not similar_hours_2.empty else None
    hourly_avg_3 = similar_hours_3.groupby("hour")["validations"].mean() if not similar_hours_3.empty else None
    hourly_avg_4 = similar_hours_4.groupby("hour")["validations"].mean() if not similar_hours_4.empty else None

    hourly_avg = pd.Series(dtype=float)

    for hour in range(24):
        values = []
        weights = []

        if hourly_avg_1 is not None and hour in hourly_avg_1:
            values.append(hourly_avg_1[hour])
            weights.append(0.5)

        if hourly_avg_4 is not None and hour in hourly_avg_4:
            values.append(hourly_avg_4[hour])
            weights.append(0.3)

        if hourly_avg_3 is not None and hour in hourly_avg_3:
            values.append(hourly_avg_3[hour])
            weights.append(0.15)

        if hourly_avg_2 is not None and hour in hourly_avg_2:
            values.append(hourly_avg_2[hour])
            weights.append(0.05)

        if values:
            weights = [w / sum(weights) for w in weights]
            hourly_avg[hour] = sum(v * w for v, w in zip(values, weights))
        else:
            hourly_avg[hour] = 0

    logger.info("\nWeighted average hourly profile (average validations per hour):")
    hourly_profile_info = ""
    for hour, avg in hourly_avg.items():
        hourly_profile_info += f"{hour}h: {avg:.0f} validations on average\n"
    logger.info(hourly_profile_info)

    last_saturdays = (
        data_df[(data_df["month"] == current_month) & (data_df["day_of_week"] == current_day_of_week)]
        .sort_index()
        .tail(24 * 4)
    )

    if len(last_saturdays) < 48:
        last_date = data_df.index.max()
        four_weeks_ago = last_date - timedelta(days=28)
        last_saturdays = data_df[data_df.index >= four_weeks_ago]
        logger.info(f"Using data from the last 4 weeks (not enough Saturdays in May)")
    else:
        logger.info(f"Using data from the last Saturdays in May")

    recent_data = last_saturdays["validations"]

    arima_forecast = None
    arima_confidence = 0
    try:
        arima_model = ARIMA(recent_data, order=(2, 1, 2))
        arima_results = arima_model.fit()

        arima_forecast = arima_results.forecast(steps=2)
        logger.info("\nARIMA predictions for the next 2 hours:")
        logger.info(str(arima_forecast))

        current_hour_historical = hourly_avg.get(current_hour, 0)
        next_hour_historical = hourly_avg.get((current_hour + 1) % 24, 0)

        if current_hour_historical > 0 and arima_forecast.iloc[0] > 0:
            current_ratio = min(
                arima_forecast.iloc[0] / current_hour_historical, current_hour_historical / arima_forecast.iloc[0]
            )
        else:
            current_ratio = 0

        if next_hour_historical > 0 and arima_forecast.iloc[1] > 0:
            next_ratio = min(
                arima_forecast.iloc[1] / next_hour_historical, next_hour_historical / arima_forecast.iloc[1]
            )
        else:
            next_ratio = 0

        arima_confidence = (current_ratio + next_ratio) / 2 if not np.isnan(current_ratio + next_ratio) else 0
        logger.info(f"Confidence in ARIMA predictions: {arima_confidence:.2f}")

    except Exception as e:
        logger.error(f"Error in ARIMA prediction: {e}")
        arima_confidence = 0

    recent_current_hour = data_df[data_df["hour"] == current_hour].tail(3)["validations"]
    recent_next_hour = data_df[data_df["hour"] == (current_hour + 1) % 24].tail(3)["validations"]

    recent_mean_current = recent_current_hour.mean() if len(recent_current_hour) > 0 else None
    recent_mean_next = recent_next_hour.mean() if len(recent_next_hour) > 0 else None

    logger.info("\nAverage of the last 3 observations:")
    recent_mean_info = ""
    if recent_mean_current is not None:
        recent_mean_info += f"- {current_hour}h: {recent_mean_current:.0f}\n"
    else:
        recent_mean_info += f"- {current_hour}h: N/A\n"

    if recent_mean_next is not None:
        recent_mean_info += f"- {(current_hour + 1) % 24}h: {recent_mean_next:.0f}"
    else:
        recent_mean_info += f"- {(current_hour + 1) % 24}h: N/A"

    logger.info(recent_mean_info)

    current_hour_start = current_time.replace(minute=0, second=0, microsecond=0)
    minutes_elapsed = current_time.minute
    minutes_remaining = 60 - minutes_elapsed
    fraction_remaining = minutes_remaining / 60

    next_hour = current_hour_start + timedelta(hours=1)

    weights = {"historical": 0.8, "recent": 0.1, "arima": 0.1 * min(1, arima_confidence)}

    total_weight = sum(weights.values())
    weights = {k: v / total_weight for k, v in weights.items()}

    logger.info("\nMethod weighting:")
    weights_info = ""
    for method, weight in weights.items():
        weights_info += f"- {method}: {weight:.1%}\n"
    logger.info(weights_info)

    current_hour_pred = 0
    next_hour_pred = 0

    current_hour_pred += hourly_avg.get(current_hour, 0) * weights["historical"]
    next_hour_pred += hourly_avg.get((current_hour + 1) % 24, 0) * weights["historical"]

    if recent_mean_current is not None:
        current_hour_pred += recent_mean_current * weights["recent"]
    else:
        current_hour_pred += hourly_avg.get(current_hour, 0) * weights["recent"]

    if recent_mean_next is not None:
        next_hour_pred += recent_mean_next * weights["recent"]
    else:
        next_hour_pred += hourly_avg.get((current_hour + 1) % 24, 0) * weights["recent"]

    if arima_forecast is not None and arima_confidence > 0.3:
        if not np.isnan(arima_forecast.iloc[0]) and 0 <= arima_forecast.iloc[0] <= 1000:
            current_hour_pred += arima_forecast.iloc[0] * weights["arima"]
        if not np.isnan(arima_forecast.iloc[1]) and 0 <= arima_forecast.iloc[1] <= 1000:
            next_hour_pred += arima_forecast.iloc[1] * weights["arima"]

    predictions = np.array([current_hour_pred, next_hour_pred])

    forecast_index = [current_hour_start, next_hour]
    forecast_df = pd.DataFrame({"forecast": predictions, "forecast_complete": predictions.copy()}, index=forecast_index)

    forecast_df.iloc[0, 0] *= fraction_remaining
    logger.info(
        f"\nAdjustment for current hour: {minutes_remaining} minutes remaining ({fraction_remaining:.1%} of the hour)"
    )

    forecast_df["forecast"] = forecast_df["forecast"].round().astype(int)
    forecast_df["forecast_complete"] = forecast_df["forecast_complete"].round().astype(int)

    total_validations = forecast_df["forecast"].sum()

    logger.info("\nValidation predictions for the next hours:")
    predictions_info = ""
    for i, (idx, row) in enumerate(forecast_df.iterrows()):
        if i == 0:
            predictions_info += f"- {idx.strftime('%H:%M')} : {int(row['forecast'])} validations (remainder of hour, complete hourly value: {int(row['forecast_complete'])})\n"
        else:
            predictions_info += f"- {idx.strftime('%H:%M')} : {int(row['forecast'])} validations\n"
    logger.info(predictions_info)

    end_time = next_hour + timedelta(minutes=59)
    logger.info(
        f"\nTotal predicted validations between {current_time.strftime('%H:%M')} and {end_time.strftime('%H:%M')}: {int(total_validations)}"
    )

    return forecast_df, total_validations
