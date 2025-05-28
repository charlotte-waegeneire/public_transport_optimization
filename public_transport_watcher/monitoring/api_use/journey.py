import streamlit as st

from public_transport_watcher.monitoring.template.display_metrics_container import display_metric_container
from public_transport_watcher.monitoring.template.format_metrics import format_metric
from public_transport_watcher.utils import get_query_result


def _display_paris_map():
    """Display Paris map with search hotspots using st.map()."""
    try:
        map_data = get_query_result("get_coordinates_heatmap")

        if map_data is None or map_data.empty:
            st.warning("Aucune donnée retournée par la requête")
            return

        required_cols = ["latitude", "longitude", "request_count"]
        if not all(col in map_data.columns for col in required_cols):
            st.error(f"Colonnes manquantes: {[col for col in required_cols if col not in map_data.columns]}")
            return

        display_data = map_data.rename(columns={"latitude": "lat", "longitude": "lon"}).copy()
        if len(display_data) > 1000:
            display_data = display_data.nlargest(1000, "request_count")

        if len(display_data) > 1000:
            display_data = display_data.nlargest(1000, "request_count")

        min_size, max_size = 10, 100
        min_requests = display_data["request_count"].min()
        max_requests = display_data["request_count"].max()

        if max_requests > min_requests:
            display_data["size"] = (display_data["request_count"] - min_requests) / (max_requests - min_requests) * (
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

        cols = st.columns(3)
        for col, (label, value) in zip(cols, metrics):
            with col:
                display_metric_container(label, value)

    except Exception as e:
        st.error(f"Erreur lors de l'affichage de la carte : {str(e)}")


def journey_search():
    """Main dashboard function."""
    st.title("Dashboard de Monitoring API")

    sections = [
        ("🗺️ Carte des recherches à Paris", None, _display_paris_map),
    ]

    for header, subheader, func in sections:
        if header:
            st.header(header)
        if subheader:
            st.subheader(subheader)
        func()
