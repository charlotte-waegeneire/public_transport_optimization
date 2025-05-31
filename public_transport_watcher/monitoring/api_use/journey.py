import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from public_transport_watcher.monitoring.template import get_safe_query_execution
from public_transport_watcher.monitoring.template.display_metrics_container import display_metric_container
from public_transport_watcher.monitoring.template.format_metrics import format_metric
from public_transport_watcher.utils import get_query_result


class DashboardHelpers:
    """Utility class for common dashboard functions"""

    @staticmethod
    def safe_execute_with_validation(query_name, data_name, required_cols=None):
        """Execute a query and validate returned data"""
        try:
            data = get_safe_query_execution(query_name, data_name)

            if data is None or data.empty:
                st.warning(f"Aucune donnée retournée pour {data_name}")
                return None

            if required_cols and not all(col in data.columns for col in required_cols):
                missing = [col for col in required_cols if col not in data.columns]
                st.error(f"Colonnes manquantes: {missing}")
                return None

            return data
        except Exception as e:
            st.error(f"Erreur lors de l'exécution de {query_name}: {str(e)}")
            return None

    @staticmethod
    def create_stations_dataframe(stations_data):
        """Enrich station data with calculated metrics"""
        stations_data["total_usage"] = stations_data["departures"] + stations_data["arrivals"]
        stations_data["balance"] = stations_data["departures"] - stations_data["arrivals"]
        stations_data["balance_abs"] = abs(stations_data["balance"])
        return stations_data

    @staticmethod
    def create_metrics_row(metrics_list):
        """Display a row of metrics in columns"""
        cols = st.columns(len(metrics_list))
        for col, (label, value) in zip(cols, metrics_list):
            with col:
                display_metric_container(label, value)


def _display_key_metrics():
    """Display key dashboard metrics"""
    try:
        stations_data = get_query_result("get_response_stations")

        if stations_data is None or stations_data.empty:
            st.warning("Aucune donnée de station pour les métriques")
            return

        stations_data = DashboardHelpers.create_stations_dataframe(stations_data)
        total_trips = stations_data["total_usage"].sum() // 2

        col1, col2 = st.columns([2, 1])
        with col1:
            display_metric_container("Station la plus recherchée", stations_data.iloc[0]["station_name"])
        with col2:
            display_metric_container("Nombre de trajets recherchés", format_metric(int(total_trips)))

    except Exception as e:
        st.error(f"Erreur lors de l'affichage des métriques : {str(e)}")


def _display_paris_map():
    """Display Paris map with search points"""
    map_data = DashboardHelpers.safe_execute_with_validation(
        "get_coordinates_heatmap", "Données de la carte", ["latitude", "longitude", "request_count"]
    )

    if map_data is None:
        return

    display_data = map_data.rename(columns={"latitude": "lat", "longitude": "lon"}).copy()
    if len(display_data) > 1000:
        display_data = display_data.nlargest(1000, "request_count")

    min_requests, max_requests = display_data["request_count"].min(), display_data["request_count"].max()
    min_size, max_size = 10, 100

    if max_requests > min_requests:
        size_range = max_requests - min_requests
        display_data["size"] = (display_data["request_count"] - min_requests) / size_range * (
            max_size - min_size
        ) + min_size
    else:
        display_data["size"] = min_size

    st.map(display_data, size="size", zoom=11)

    metrics = [
        ("Nombre de lieux recherchés", format_metric(len(display_data))),
        ("Nombre de requêtes minimal", format_metric(min_requests)),
        ("Nombre de requêtes maximal", format_metric(max_requests)),
    ]
    DashboardHelpers.create_metrics_row(metrics)


def _create_stacked_bar_chart(top_stations):
    """Create stacked bar chart for stations"""
    fig = go.Figure()

    traces_config = [("Départs", "departures", "#ff6b6b"), ("Arrivées", "arrivals", "#4ecdc4")]

    for name, column, color in traces_config:
        fig.add_trace(
            go.Bar(
                name=name, y=top_stations["station_name"], x=top_stations[column], orientation="h", marker_color=color
            )
        )

    fig.update_layout(barmode="stack", margin=dict(t=0))
    return fig


def _create_sunburst_chart(stations_data):
    """Create sunburst chart for departures/arrivals distribution"""
    pie_data = []
    for _, row in stations_data.iterrows():
        pie_data.extend(
            [
                {"station": row["station_name"], "type": "Départs", "count": row["departures"]},
                {"station": row["station_name"], "type": "Arrivées", "count": row["arrivals"]},
            ]
        )

    pie_df = pd.DataFrame(pie_data)
    fig = px.sunburst(
        pie_df,
        path=["type", "station"],
        values="count",
        color="type",
        color_discrete_map={"Départs": "#ff6b6b", "Arrivées": "#4ecdc4"},
    )

    fig.update_traces(textinfo="label", hovertemplate=None, hoverinfo="skip")
    fig.update_layout(margin=dict(t=0, b=20, l=20, r=20))
    return fig


def _create_balance_scatter_chart(top_stations):
    """Create scatter chart for departures/arrivals balance"""
    fig = go.Figure()

    balance_config = [
        (top_stations[top_stations["balance"] > 0], "Plus de départs", "#ff6b6b"),
        (top_stations[top_stations["balance"] < 0], "Plus d'arrivées", "#4ecdc4"),
        (top_stations[top_stations["balance"] == 0], "Équilibrées", "#95a5a6"),
    ]

    for data_subset, name, color in balance_config:
        if not data_subset.empty:
            fig.add_trace(
                go.Scatter(
                    x=data_subset["departures"],
                    y=data_subset["arrivals"],
                    mode="markers",
                    text=data_subset["station_name"],
                    textposition="top center",
                    marker=dict(size=12, color=color, opacity=0.8),
                    name=name,
                    hovertemplate="<b>%{text}</b><br>Départs: %{x}<br>Arrivées: %{y}<extra></extra>",
                )
            )

    if not top_stations.empty:
        max_val = max(top_stations["departures"].max(), top_stations["arrivals"].max())
        fig.add_trace(
            go.Scatter(
                x=[0, max_val],
                y=[0, max_val],
                mode="lines",
                line=dict(dash="dash", color="gray", width=2),
                name="Équilibre parfait",
                showlegend=False,
            )
        )

    fig.update_layout(
        xaxis_title="Nombre de départs",
        yaxis_title="Nombre d'arrivées",
        margin=dict(t=0, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        hovermode="closest",
    )
    return fig


def _display_stations_analysis():
    """Display complete stations analysis"""
    stations_data = DashboardHelpers.safe_execute_with_validation(
        "get_response_stations", "Données d'analyse des stations", ["station_name", "departures", "arrivals"]
    )

    if stations_data is None:
        return

    stations_data = DashboardHelpers.create_stations_dataframe(stations_data)
    total_stations = len(stations_data)
    top_stations = stations_data.head(20)

    st.subheader("Top 20 des stations les plus recherchées")
    st.plotly_chart(_create_stacked_bar_chart(top_stations), use_container_width=True)

    st.subheader("Répartition Départs vs Arrivées")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.plotly_chart(_create_sunburst_chart(stations_data), use_container_width=True)

    with col2:
        st.plotly_chart(_create_balance_scatter_chart(top_stations), use_container_width=True)

    st.subheader("Tableau détaillé des stations")

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        min_usage = st.slider("Usage minimum", 0, int(stations_data["total_usage"].max()), 0)
    with col_filter2:
        search_station = st.text_input("Rechercher une station")

    filtered_data = stations_data[stations_data["total_usage"] >= min_usage].copy()
    if search_station:
        filtered_data = filtered_data[filtered_data["station_name"].str.contains(search_station, case=False, na=False)]

    display_data = filtered_data[["station_name", "departures", "arrivals", "total_usage"]].copy()
    display_data.columns = ["Station", "Départs", "Arrivées", "Total"]

    st.dataframe(display_data, use_container_width=True, hide_index=True)
    st.caption(f"Affichage de {len(filtered_data)} stations sur {total_stations} total")


def journey_search():
    """Main dashboard function."""
    st.title("Statistiques des recherches API")

    sections = [
        ("📊 Vue d'ensemble", "Métriques clés", _display_key_metrics),
        ("🗺️ Carte des recherches à Paris", None, _display_paris_map),
        ("🚇 Analyse des stations", None, _display_stations_analysis),
    ]

    for header, subheader, func in sections:
        if header:
            st.header(header)
        if subheader:
            st.subheader(subheader)
        func()


if __name__ == "__main__":
    journey_search()
