import time

import altair as alt
import plotly.express as px
import streamlit as st

from public_transport_watcher.monitoring.template import get_safe_query_execution
from public_transport_watcher.utils import get_query_result

# Constantes
FR_MONTHS = {
    1: "Janvier",
    2: "Février",
    3: "Mars",
    4: "Avril",
    5: "Mai",
    6: "Juin",
    7: "Juillet",
    8: "Août",
    9: "Septembre",
    10: "Octobre",
    11: "Novembre",
    12: "Décembre",
}

DAYS_OF_WEEK = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def _create_bar_chart(data, x_col, y_col, x_title, y_title):
    """Creates a standardized bar chart."""
    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(x_col, sort=None, title=x_title),
            y=alt.Y(y_col, title=y_title),
        )
    )


def _display_top_charts():
    """Displays Top 10 lines and stations charts."""
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 lignes")
        lines_traffic = get_safe_query_execution("get_top_10_lines", "Top 10 lignes")
        if lines_traffic is not None:
            chart = _create_bar_chart(lines_traffic, "line_name", "total_validations", "Ligne", "Nombre de validations")
            st.altair_chart(chart, use_container_width=True)

    with col2:
        st.subheader("Top 10 Stations")
        stations_traffic = get_safe_query_execution("get_top_10_stations", "Top 10 stations")
        if stations_traffic is not None:
            chart = _create_bar_chart(stations_traffic, "station_name", "count", "Station", "Nombre de validations")
            st.altair_chart(chart, use_container_width=True)


def _filter_transport_data(data, transport_type):
    """Filters data according to the selected transport type."""
    if transport_type == "Tous":
        return data.groupby(["year", "month"], as_index=False)["count"].sum()
    return data[data["transport_type"] == transport_type]


def _prepare_monthly_data(data):
    """Prepares data for monthly display."""
    data = data.copy()
    data["fr_months"] = data["month"].map(FR_MONTHS) + " " + data["year"].astype(int).astype(str)
    return data.sort_values(["year", "month"])


def _create_monthly_evolution_chart():
    """Creates the monthly validation evolution chart."""

    validations_data = get_safe_query_execution("get_validations_per_month_year", "Évolution mensuelle des validations")
    if validations_data is None or validations_data.empty:
        st.error("Aucune donnée disponible")
        return

    selected_transport = st.selectbox(
        "Type de transport :",
        ["Tous"] + sorted(validations_data["transport_type"].unique()),
        key="monthly_evolution_transport_filter",
    )

    filtered_data = _filter_transport_data(validations_data, selected_transport)

    if filtered_data.empty:
        st.info("Aucune donnée pour ce type de transport.")
        return

    chart_data = _prepare_monthly_data(filtered_data)

    chart = (
        alt.Chart(chart_data)
        .mark_line(point=True)
        .encode(
            x=alt.X("fr_months:O", title="Date", axis=alt.Axis(labelAngle=-45), sort=None),
            y=alt.Y("count:Q", title="Nombre de validations"),
            tooltip=[
                alt.Tooltip("fr_months:N", title="Mois"),
                alt.Tooltip("count:Q", format=",.0f", title="Validations"),
            ],
        )
    )

    st.altair_chart(chart, use_container_width=True)


def _create_hourly_heatmap():
    """Creates the hourly traffic frequency heatmap."""
    hourly_traffic = get_safe_query_execution("get_hourly_traffic_heatmap", "Fréquentation par créneau horaire")
    if hourly_traffic is None:
        return

    heatmap_data = hourly_traffic.pivot(index="day_of_week", columns="hour_bin", values="avg_validations").fillna(0)

    fig_heatmap = px.imshow(
        heatmap_data,
        labels=dict(x="Heure", y="Jour de la semaine", color="Validations moyennes"),
        color_continuous_scale="Viridis",
        aspect="auto",
    )

    fig_heatmap.update_layout(
        yaxis=dict(tickvals=list(range(7)), ticktext=DAYS_OF_WEEK), margin=dict(t=10, b=40, l=80, r=10)
    )

    st.plotly_chart(fig_heatmap, use_container_width=True)


def _display_key_metrics():
    """Display key metrics."""

    col1, col2, col3, col4 = st.columns(4)
    metrics = get_query_result("get_dashboard_metrics")

    def format_metric(value):
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        else:
            return f"{value:,.0f}".replace(",", " ")

    with col1:
        with st.container(border=True):
            st.metric("Total validations", format_metric(metrics["total_validations"][0]))

    with col2:
        with st.container(border=True):
            st.metric("Stations actives", format_metric(metrics["active_stations"][0]))

    with col3:
        with st.container(border=True):
            st.metric("Lignes en service", format_metric(metrics["active_lines"][0]))

    with col4:
        with st.container(border=True):
            st.metric("Valid./jour (moy.)", format_metric(metrics["avg_daily_validations"][0]))


def dashboard():
    """Main dashboard function."""
    st.title("Utilisation des transports publics")
    st.header("📊 Vue d'ensemble")
    st.subheader("Métriques clés")
    _display_key_metrics()
    _display_top_charts()

    st.header("📈 Évolution mensuelle des validations")
    _create_monthly_evolution_chart()

    st.header("🕐 Fréquentation par créneau horaire")
    _create_hourly_heatmap()


if __name__ == "__main__":
    dashboard()
