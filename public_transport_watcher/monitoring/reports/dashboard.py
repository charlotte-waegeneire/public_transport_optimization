import pandas as pd
import streamlit as st

from public_transport_watcher.utils import get_query_result


def dashboard():
    st.title("Dashboard")

    st.title("Top 10 Stations")
    top_10_stations = get_query_result("get_top_10_stations")
    st.bar_chart(top_10_stations, x="station_name", y="count")

    st.title("Validations per Month and Year")
    validations_per_month_year = get_query_result("get_validations_per_month_year")
    validations_per_month_year["date"] = pd.to_datetime(
        validations_per_month_year["year"].astype(int).astype(str)
        + "-"
        + validations_per_month_year["month"].astype(int).astype(str)
    )
    st.line_chart(validations_per_month_year, x="date", y="count")
