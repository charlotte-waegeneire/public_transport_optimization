import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from public_transport_watcher.monitoring.template import get_safe_query_execution
from public_transport_watcher.monitoring.template.display_metrics_container import display_metric_container
from public_transport_watcher.monitoring.template.format_metrics import format_metric
from public_transport_watcher.utils import get_query_result


def create_stations_dataframe(stations_data):
    """Enrich station data with calculated metrics"""
    stations_data["total_usage"] = stations_data["departures"] + stations_data["arrivals"]
    stations_data["balance"] = stations_data["departures"] - stations_data["arrivals"]
    stations_data["balance_abs"] = abs(stations_data["balance"])
    return stations_data


def create_metrics_row(metrics_list):
    """Display a row of metrics in columns"""
    cols = st.columns(len(metrics_list))
    for col, (label, value) in zip(cols, metrics_list):
        with col:
            display_metric_container(label, value)


def normalize_map_size(data, column, min_size=10, max_size=100):
    """Normalize values for map point sizing"""
    min_val, max_val = data[column].min(), data[column].max()

    if max_val > min_val:
        size_range = max_val - min_val
        return (data[column] - min_val) / size_range * (max_size - min_size) + min_size
    else:
        return min_size


def _display_key_metrics():
    """Display key dashboard metrics"""
    try:
        stations_data = get_query_result("get_response_stations")

        if stations_data is None or stations_data.empty:
            st.warning("Aucune donnée de station pour les métriques")
            return

        stations_data = create_stations_dataframe(stations_data)
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
    map_data = get_safe_query_execution("get_coordinates_heatmap", "Données de la carte")

    if map_data is None or map_data.empty:
        return

    required_cols = ["latitude", "longitude", "request_count"]
    if not all(col in map_data.columns for col in required_cols):
        missing = [col for col in required_cols if col not in map_data.columns]
        st.error(f"Colonnes manquantes: {missing}")
        return

    display_data = map_data.rename(columns={"latitude": "lat", "longitude": "lon"}).copy()
    if len(display_data) > 1000:
        display_data = display_data.nlargest(1000, "request_count")

    min_requests, max_requests = display_data["request_count"].min(), display_data["request_count"].max()
    display_data["size"] = normalize_map_size(display_data, "request_count")

    st.map(display_data, size="size", zoom=11)

    metrics = [
        ("Nombre de lieux recherchés", format_metric(len(display_data))),
        ("Nombre de requêtes minimal", format_metric(min_requests)),
        ("Nombre de requêtes maximal", format_metric(max_requests)),
    ]
    create_metrics_row(metrics)


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


def _display_stations_analysis():
    """Display complete stations analysis"""
    stations_data = get_safe_query_execution("get_response_stations", "Données d'analyse des stations")

    if stations_data is None or stations_data.empty:
        return

    required_cols = ["station_name", "departures", "arrivals"]
    if not all(col in stations_data.columns for col in required_cols):
        missing = [col for col in required_cols if col not in stations_data.columns]
        st.error(f"Colonnes manquantes: {missing}")
        return

    stations_data = create_stations_dataframe(stations_data)
    total_stations = len(stations_data)
    top_stations = stations_data.head(20)

    st.subheader("Répartition des stations de départs et d'arrivées")
    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(_create_stacked_bar_chart(top_stations), use_container_width=True)

    with col2:
        st.plotly_chart(_create_sunburst_chart(stations_data), use_container_width=True)

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
