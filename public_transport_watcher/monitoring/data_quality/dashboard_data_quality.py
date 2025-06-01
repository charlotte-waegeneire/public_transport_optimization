import streamlit as st
import plotly.express as px
from public_transport_watcher.monitoring.template import get_safe_query_execution
from public_transport_watcher.monitoring.template.display_metrics_container import display_metric_container
from public_transport_watcher.monitoring.template.format_metrics import format_metric


def _create_traffic_chart(traffic_data):
    """Create traffic evolution chart with average line."""
    average = traffic_data["traffic_records"].mean()

    fig = px.line(traffic_data, x="month", y="traffic_records", markers=True)
    fig.add_hline(
        y=average,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Moyenne: {format_metric(average)}",
        annotation_position="top right",
    )
    fig.update_layout(
        xaxis_title="Mois",
        yaxis_title="Nombre d'enregistrements",
        hovermode="x unified",
        margin=dict(t=0),
    )

    return fig


def _display_completeness_metrics(completeness_data):
    """Display data completeness metrics in the sidebar."""
    recent_data = completeness_data.head(12)
    total_months = len(recent_data)

    if total_months == 0:
        return

    months_with_traffic = recent_data["has_traffic"].sum()
    months_with_schedule = recent_data["has_schedule"].sum()

    traffic_completeness_pct = (months_with_traffic / total_months) * 100
    schedule_completeness_pct = (months_with_schedule / total_months) * 100

    display_metric_container("Mois analysés", str(total_months))
    display_metric_container(
        "Complétude données Trafic", f"{traffic_completeness_pct:.1f}%", percentage=traffic_completeness_pct
    )
    display_metric_container(
        "Complétude données Horaires", f"{schedule_completeness_pct:.1f}%", percentage=schedule_completeness_pct
    )


def _data_quality_overview():
    """Display overview with chart on left and metrics on right."""
    col_graph, col_metrics = st.columns([2, 1])

    with col_graph:
        st.subheader("Évolution du volume de données")

        traffic_data = get_safe_query_execution("monthly_data_completeness", "Données de trafic")

        if traffic_data is not None and not traffic_data.empty:
            fig_traffic = _create_traffic_chart(traffic_data)
            st.plotly_chart(fig_traffic, use_container_width=True)

    with col_metrics:
        st.subheader("Métriques clés")

        completeness_data = get_safe_query_execution("data_completeness_overview", "Taux de complétude")

        if completeness_data is not None and not completeness_data.empty:
            _display_completeness_metrics(completeness_data)


def dashboard_data_quality():
    """Main dashboard function for data quality monitoring."""
    st.title("Qualité des données")

    _data_quality_overview()


if __name__ == "__main__":
    dashboard_data_quality()
