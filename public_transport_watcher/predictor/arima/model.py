from public_transport_watcher.logging_config import get_logger
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX

logger = get_logger()


def build_arima_model(timeseries):
    """
    Builds and fits an ARIMA model on a time series.

    Args:
        timeseries (Series): Prepared time series

    Returns:
        SARIMAXResultsWrapper: Fitted ARIMA model
    """
    model = SARIMAX(
        timeseries,
        order=(1, 1, 1)
    )

    return model.fit(disp=False, method='powell', maxiter=200)


def predict_traffic(model_fit, timeseries, steps=1):
    """
    Generates predictions from a fitted ARIMA model.

    Args:
        model_fit (SARIMAXResultsWrapper): Fitted ARIMA model
        timeseries (Series): Time series used for fitting
        steps (int): Number of periods to forecast

    Returns:
        tuple: (Predicted values, confidence intervals)
    """
    forecast = model_fit.get_forecast(steps=steps)
    forecast_means = forecast.predicted_mean.values
    conf_ints = forecast.conf_int().values

    forecast_means = np.maximum(1, np.round(forecast_means))
    conf_ints = np.maximum(0, np.round(conf_ints))

    return forecast_means, conf_ints