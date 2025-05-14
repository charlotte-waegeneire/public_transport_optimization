import calendar
import os

import matplotlib.pyplot as plt
import numpy as np


def visualize_predictions(station_id, hourly_avg, forecast_df, current_time, data_df, save_dir="graphs"):
    """
        Generate and save validation prediction chart for a specific station.

        Args:
            station_id (str): Station identifier
            hourly_avg (Dict[int, float]): Average validations by hour (0-23)
            forecast_df (pd.DataFrame): Predictions with 'forecast_complete' column
            current_time (datetime): Current time
            data_df (pd.DataFrame): Historical data with 'hour' and 'validations' columns
            save_dir (str, optional): Directory to save charts. Defaults to "graphs".

        Returns:
            str: Path to saved chart file
        """
    os.makedirs(save_dir, exist_ok=True)

    current_hour = current_time.hour
    current_month = current_time.month
    current_day_of_week = current_time.weekday()

    plt.figure(figsize=(14, 8))

    hours = list(range(24))
    avg_values = [hourly_avg.get(hour, 0) for hour in hours]
    plt.plot(hours, avg_values, "b-", label="Average hourly profile", alpha=0.7, linewidth=2)

    plt.axvline(x=current_hour, color="green", linestyle=":", alpha=0.5, label="Current hour")
    plt.axvline(x=(current_hour + 1) % 24, color="green", linestyle=":", alpha=0.5)

    for h, color, label in [
        (current_hour, "blue", f"Historical {current_hour}h"),
        ((current_hour + 1) % 24, "purple", f"Historical {(current_hour + 1) % 24}h"),
    ]:
        recent_values = data_df[data_df["hour"] == h].tail(5)["validations"].values
        if len(recent_values) > 0:
            plt.scatter([h] * len(recent_values), recent_values, color=color, marker="x", label=label, s=80)

    prediction_hours = [current_hour, (current_hour + 1) % 24]
    prediction_values = forecast_df["forecast_complete"].values

    plt.scatter(prediction_hours, prediction_values, color="red", marker="o", s=120, label="Predictions", zorder=5)

    for hour, value in zip(prediction_hours, prediction_values):
        plt.annotate(
            f"{int(value)}", (hour, value), textcoords="offset points", xytext=(0, 10), ha="center", fontweight="bold"
        )

    title = (
        f"Validation Predictions - Station {station_id}\n"
        f"{calendar.month_name[current_month]}, {calendar.day_name[current_day_of_week]}"
    )

    plt.title(title, fontsize=14, fontweight="bold")
    plt.xlabel("Hour of the day", fontsize=12)
    plt.ylabel("Number of validations", fontsize=12)

    plt.grid(True, alpha=0.3)
    plt.legend(loc="upper left", fontsize=10)
    plt.xticks(np.arange(0, 24, 1))

    max_value = max(700, max(avg_values) * 1.2)
    plt.ylim(0, max_value)

    plt.tight_layout()

    timestamp = current_time.strftime("%Y%m%d_%H%M")
    filename = f"prediction_station_{station_id}_{timestamp}.png"
    filepath = os.path.join(save_dir, filename)
    plt.savefig(filepath)
    return plt
