import calendar
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.predictor.arima.preprocess_data import preprocess_data

logger = get_logger()


def _get_current_time_info():
    current_time = datetime.now()
    current_month = current_time.month
    current_day_of_week = current_time.weekday()
    current_hour = current_time.hour

    logger.info(f"Current date and time: {current_time}")
    logger.info(f"Current month: {calendar.month_name[current_month]}")
    logger.info(f"Day of the week: {calendar.day_name[current_day_of_week]}")
    logger.info(f"Hour: {current_hour}h")

    return current_time, current_month, current_day_of_week, current_hour


def _get_exact_same_days(data_df, current_month, current_day_of_week):
    exact_same_days = data_df[(data_df["month"] == current_month) & (data_df["day_of_week"] == current_day_of_week)]

    common_cat_day = exact_same_days["cat_day"].mode().iloc[0] if not exact_same_days.empty else None

    if common_cat_day:
        exact_same_days = exact_same_days[exact_same_days["cat_day"] == common_cat_day]

    return exact_same_days


def _get_recent_data(data_df, days=28):
    last_date = data_df.index.max()
    days_ago = last_date - timedelta(days=days)
    return data_df[data_df.index >= days_ago]


def _calculate_hourly_averages(exact_same_days):
    if exact_same_days.empty:
        return pd.Series(dtype=float), pd.Series(dtype=float)

    # Add a weighting column based on recency
    last_date = exact_same_days.index.max()
    days_ago = (last_date - exact_same_days.index).days
    exact_same_days["time_weight"] = np.exp(-0.05 * days_ago)  # Exponential weight decreasing with time

    hourly_avg_weighted = exact_same_days.groupby("hour").apply(
        lambda x: np.average(x["validations"], weights=x["time_weight"])
    )

    hourly_avg = exact_same_days.groupby("hour")["validations"].mean()

    logger.info("\nComparison of hourly averages:")
    for hour in range(24):
        if hour in hourly_avg:
            weighted_val = hourly_avg_weighted.get(hour, 0)
            normal_val = hourly_avg.get(hour, 0)
            logger.info(f"{hour}h: {normal_val:.0f} (simple average) vs {weighted_val:.0f} (time-weighted average)")

    return hourly_avg_weighted, hourly_avg


def _apply_arima_model(recent_data, current_hour, arima_params, hourly_avg_weighted):
    try:
        recent_hour_data = recent_data[recent_data["hour"] == current_hour]["validations"]

        if len(recent_hour_data) >= 20:  # Enough data for ARIMA
            p, d, q = arima_params
            arima_model = ARIMA(recent_hour_data, order=(p, d, q))
            arima_results = arima_model.fit()

            arima_forecast = arima_results.forecast(steps=2)
            logger.info(f"\nARIMA{arima_params} predictions for next 2 hours:")
            logger.info(str(arima_forecast))

            if current_hour in hourly_avg_weighted and hourly_avg_weighted[current_hour] > 0:
                arima_ratio = min(
                    arima_forecast.iloc[0] / hourly_avg_weighted[current_hour],
                    hourly_avg_weighted[current_hour] / arima_forecast.iloc[0],
                )
                arima_confidence = arima_ratio if not np.isnan(arima_ratio) else 0
            else:
                arima_confidence = 0

            logger.info(f"Confidence in ARIMA predictions: {arima_confidence:.2f}")
            return arima_forecast, arima_confidence
        else:
            logger.info("Not enough recent data for ARIMA")
            return None, 0
    except Exception as e:
        logger.error(f"Error in ARIMA prediction: {e}")
        return None, 0


def _get_recent_observations(recent_data, hours):
    very_recent_obs = {}

    for hour in hours:
        hour_data = recent_data[recent_data["hour"] == hour]["validations"].tail(3)
        if not hour_data.empty:
            very_recent_obs[hour] = hour_data.mean()
            logger.info(f"Average of last 3 observations for {hour}h: {very_recent_obs[hour]:.0f}")
        else:
            very_recent_obs[hour] = None

    return very_recent_obs


def _calculate_weights(hourly_avg_weighted, very_recent_obs, arima_confidence, hours):
    # Analyze variance between recent and historical data
    recent_variance = {}
    for hour in hours:
        if hour in hourly_avg_weighted and hour in very_recent_obs and very_recent_obs[hour] is not None:
            historical = hourly_avg_weighted[hour]
            recent = very_recent_obs[hour]

            if historical > 0 and recent > 0:
                ratio = min(historical / recent, recent / historical)
                recent_variance[hour] = ratio
            else:
                recent_variance[hour] = 0

    avg_consistency = sum(recent_variance.values()) / len(recent_variance) if recent_variance else 0

    historical_weight = min(0.8, 0.5 + 0.3 * avg_consistency)
    recent_weight = 0.2 + 0.2 * (1 - avg_consistency)
    arima_weight = 0.1 * arima_confidence

    total_weight = historical_weight + recent_weight + arima_weight
    weights = {
        "historical": historical_weight / total_weight,
        "recent": recent_weight / total_weight,
        "arima": arima_weight / total_weight,
    }

    return weights


def _calculate_predictions(hourly_avg_weighted, very_recent_obs, arima_forecast, weights, hours):
    predictions = []

    for i, hour in enumerate(hours):
        pred = 0

        if hour in hourly_avg_weighted:
            pred += hourly_avg_weighted[hour] * weights["historical"]

        if hour in very_recent_obs and very_recent_obs[hour] is not None:
            pred += very_recent_obs[hour] * weights["recent"]
        elif hour in hourly_avg_weighted:
            pred += hourly_avg_weighted[hour] * weights["recent"]

        if arima_forecast is not None and i < len(arima_forecast) and weights["arima"] > 0:
            if not np.isnan(arima_forecast.iloc[i]) and 0 <= arima_forecast.iloc[i] <= 1000:
                pred += arima_forecast.iloc[i] * weights["arima"]

        predictions.append(pred)

    return predictions


def _create_forecast_dataframe(predictions, current_time):
    current_hour_start = current_time.replace(minute=0, second=0, microsecond=0)
    next_hour = current_hour_start + timedelta(hours=1)

    forecast_index = [current_hour_start, next_hour]
    return pd.DataFrame({"forecast": predictions.copy(), "forecast_complete": predictions.copy()}, index=forecast_index)


def _adjust_current_hour_forecast(forecast_df, current_time):
    minutes_elapsed = current_time.minute
    minutes_remaining = 60 - minutes_elapsed
    fraction_remaining = minutes_remaining / 60

    forecast_df.iloc[0, 0] *= fraction_remaining

    return forecast_df


def _finalize_forecast(forecast_df):
    forecast_df["forecast"] = forecast_df["forecast"].round().astype(int)
    forecast_df["forecast_complete"] = forecast_df["forecast_complete"].round().astype(int)

    total_validations = forecast_df["forecast"].sum()

    logger.info("\nValidation predictions for next hours:")
    for i, (idx, row) in enumerate(forecast_df.iterrows()):
        if i == 0:
            logger.info(
                f"- {idx.strftime('%H:%M')}: {int(row['forecast'])} validations "
                f"(remainder of hour, complete value: {int(row['forecast_complete'])})"
            )
        else:
            logger.info(f"- {idx.strftime('%H:%M')}: {int(row['forecast'])} validations")

    end_time = forecast_df.index[1] + timedelta(minutes=59)
    logger.info(
        f"\nTotal predicted validations between {forecast_df.index[0].strftime('%H:%M')} "
        f"and {end_time.strftime('%H:%M')}: {int(total_validations)}"
    )

    return forecast_df, total_validations


def predict_navigo_validations(df, station_id, arima_params):
    """
    Enhanced prediction model that combines historical averages, recent trends, and ARIMA models.

    Args:
        df (DataFrame): Station data
        station_id (int): Station ID
        arima_params (tuple): ARIMA parameters (p, d, q)

    Returns:
        tuple: (predictions DataFrame, total validations)
    """
    data_df = preprocess_data(df, station_id)

    current_time, current_month, current_day_of_week, current_hour = _get_current_time_info()
    exact_same_days = _get_exact_same_days(data_df, current_month, current_day_of_week)

    recent_data = _get_recent_data(data_df)

    hourly_avg_weighted, hourly_avg = _calculate_hourly_averages(exact_same_days)

    arima_forecast, arima_confidence = _apply_arima_model(recent_data, current_hour, arima_params, hourly_avg_weighted)

    recent_hours = [current_hour, (current_hour + 1) % 24]

    very_recent_obs = _get_recent_observations(recent_data, recent_hours)

    weights = _calculate_weights(hourly_avg_weighted, very_recent_obs, arima_confidence, recent_hours)

    predictions = _calculate_predictions(hourly_avg_weighted, very_recent_obs, arima_forecast, weights, recent_hours)

    forecast_df = _create_forecast_dataframe(predictions, current_time)
    forecast_df = _adjust_current_hour_forecast(forecast_df, current_time)
    forecast_df, total_validations = _finalize_forecast(forecast_df)

    return forecast_df, total_validations
