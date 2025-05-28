import streamlit as st
import plotly.express as px

from public_transport_watcher.monitoring.template.display_metrics_container import display_metric_container
from public_transport_watcher.monitoring.template.format_metrics import format_metric
from public_transport_watcher.utils import get_query_result
from public_transport_watcher.monitoring.template import get_safe_query_execution

DAYS_OF_WEEK = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

COLUMN_CONFIGS = {
    "performance": {
        "request_path": st.column_config.TextColumn("Endpoint"),
        "method": st.column_config.TextColumn("Méthode"),
        "avg_time": st.column_config.NumberColumn("Temps moyen (ms)"),
        "max_time": st.column_config.NumberColumn("Temps max (ms)"),
        "requests": st.column_config.NumberColumn("Nombre de requêtes"),
    },
    "errors": {
        "code": st.column_config.NumberColumn("Code"),
        "description": st.column_config.TextColumn("Description"),
        "error_count": st.column_config.NumberColumn("Nombre"),
        "percentage": st.column_config.NumberColumn("% du total"),
        "avg_response_time": st.column_config.NumberColumn("Temps moy. (ms)"),
    },
}


def _display_dataframe(data, format_dict, column_config_key, **kwargs):
    """Display formatted dataframe."""
    if data is not None and not data.empty:
        st.dataframe(
            data.style.format(format_dict),
            column_config=COLUMN_CONFIGS[column_config_key],
            use_container_width=True,
            hide_index=True,
            **kwargs,
        )


def _display_key_metrics():
    """Display key metrics."""
    overview = get_query_result("get_overview_stats")

    metrics = [
        ("Requêtes totales (7j)", format_metric(overview["total_requests"][0])),
        ("Nb. jours d'activité API", format_metric(overview["active_days"].iloc[0])),
        ("Temps réponse moy.", format_metric(overview["avg_response_time"].iloc[0]) + " ms"),
        ("Nombre visiteurs", format_metric(overview["unique_visitors"].iloc[0])),
    ]

    cols = st.columns(4)
    for col, (label, value) in zip(cols, metrics):
        with col:
            display_metric_container(label, value)


def _display_traffic_charts():
    """Display main traffic charts."""
    col1, col2 = st.columns([5, 3])

    with col1:
        st.subheader("Trafic par heure (24h)")
        data = get_safe_query_execution("get_requests_by_hour", "Trafic par heure (24h)")
        if data is not None and not data.empty:
            fig = px.line(
                data,
                x="hour",
                y="requests_count",
                labels={"hour": "Heure", "requests_count": "Nombre de requêtes"},
            )
            fig.update_layout(margin=dict(t=0))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        with col2:
            st.subheader("Distribution statuts")
            data = get_safe_query_execution("get_status_distribution", "Distribution des statuts")
            if data is not None and not data.empty:
                fig = px.pie(data, values="count", names="description")
                fig.update_layout(
                    legend=dict(orientation="h", yanchor="top", y=-0, xanchor="center", x=0.5), margin=dict(t=0)
                )
                st.plotly_chart(fig, use_container_width=True)


def _display_performance_table():
    """Display performance table."""
    data = get_safe_query_execution("get_endpoints_performances", "Endpoints lents")
    format_dict = {"avg_time": "{:.3f}", "max_time": "{:.3f}", "requests": "{:,}"}
    _display_dataframe(data, format_dict, "performance")


def _display_activity_heatmap():
    """Display activity heatmap with peak traffic information."""
    col1, col2 = st.columns([3, 5])

    with col1:
        st.subheader("Rush Hour")
        peak_traffic = get_safe_query_execution("get_peak_traffic_info", "Rush Hour")

        if peak_traffic is not None and not peak_traffic.empty:
            peak_info = peak_traffic.iloc[0]
            peak_day = DAYS_OF_WEEK[int(peak_info["peak_day"])]
            peak_hour = int(peak_info["peak_hour"])
            peak_requests = format_metric(int(peak_info["max_requests"]))

            with st.container(border=True):
                st.markdown("**Cette semaine :**")
                st.metric("Pic de trafic", f"{peak_day}\nà {peak_hour}h")
                st.metric("Nombre de requêtes", peak_requests)

    with col2:
        st.subheader("Trafic par créneau horaire")
        data = get_safe_query_execution("get_heatmap_data", "Trafic par créneau horaire")

        if data is not None and not data.empty:
            matrix = data.pivot(index="day_of_week", columns="hour_of_day", values="requests").fillna(0)
            matrix.index = [DAYS_OF_WEEK[int(i)] for i in matrix.index]

            fig = px.imshow(
                matrix, labels=dict(x="Heure", y="Jour", color="Requêtes"), color_continuous_scale="Viridis"
            )
            fig.update_layout(height=250, margin=dict(t=20, b=40))
            st.plotly_chart(fig, use_container_width=True)


def _display_error_analysis():
    """Display enhanced error analysis."""
    st.subheader("Évolution des erreurs par type")

    error_data = get_safe_query_execution("get_error_analysis", "Analyse des erreurs par type")
    if error_data is not None and not error_data.empty:
        fig = px.line(
            error_data,
            x="hour",
            y="error_count",
            color="error_type",
            labels={"hour": "Heure", "error_count": "Nombre d'erreurs", "error_type": "Type d'erreur"},
        )
        fig.update_layout(margin=dict(t=0))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Récapitulatif des erreurs")
    data = get_safe_query_execution("get_error_summary", "Récapitulatif des erreurs")
    format_dict = {"error_count": "{:,}", "percentage": "{:.1f}%", "avg_response_time": "{:.3f}"}
    _display_dataframe(data, format_dict, "errors")


def dashboard_api():
    """Main dashboard function."""
    st.title("Monitoring de l'API")

    sections = [
        ("📊 Vue d'ensemble", "Métriques clés", _display_key_metrics),
        (None, None, _display_traffic_charts),
        ("🚀 Performance des endpoints", None, _display_performance_table),
        ("🔥 Trafic par créneau horaire", None, _display_activity_heatmap),
        ("🚨 Monitoring des erreurs", None, _display_error_analysis),
    ]

    for header, subheader, func in sections:
        if header:
            st.header(header)
        if subheader:
            st.subheader(subheader)
        func()


if __name__ == "__main__":
    dashboard_api()
