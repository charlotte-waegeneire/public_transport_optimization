from datetime import datetime
import streamlit as st

from public_transport_watcher.utils.get_transports_icons import (
    get_line_badge_for_streamlit,
    extract_line_code_from_text,
)
from public_transport_watcher.extractor.extract.alerts import extract_alerts_data
from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_cache_info

logger = get_logger()


def get_severity_icon(message, cause=None):
    """Returns appropriate icon based on message and cause"""
    if not message:
        return ""

    if cause and "travaux" in cause.lower():
        return "🚧"

    lowered = message.lower()
    if any(word in lowered for word in ["alerte", "interrompu", "fermé"]):
        return "🚨"
    elif any(word in lowered for word in ["retard", "ralenti", "perturbé", "dévié"]):
        return "⚠️"
    return "ℹ️"


def format_cache_time(cache_time):
    """Formats cache time for display"""
    time_diff = datetime.now() - cache_time
    minutes_ago = int(time_diff.total_seconds() / 60)

    if minutes_ago < 1:
        return "À l'instant"
    elif minutes_ago == 1:
        return "Il y a 1 minute"
    elif minutes_ago < 60:
        return f"Il y a {minutes_ago} minutes"
    else:
        hours_ago = int(minutes_ago / 60)
        return f"Il y a {hours_ago} heure{'s' if hours_ago > 1 else ''}"


def alerts():
    """Main alerts display function"""
    st.title("🚦 État du trafic en Île-de-France")

    cache_time, is_cache_valid = get_cache_info()
    refresh_clicked = st.button("🔄 Actualiser")

    if cache_time:
        time_text = format_cache_time(cache_time)
        status_emoji = "📅" if is_cache_valid else "⚠️"
        status_text = "Dernière actualisation" if is_cache_valid else "Données expirées"
        st.caption(f"{status_emoji} {status_text} : {cache_time.strftime('%H:%M:%S')} ({time_text})")
    else:
        st.caption("📅 Aucune donnée en cache")

    if refresh_clicked:
        with st.spinner("🔄 Actualisation en cours..."):
            df = extract_alerts_data(force_refresh=True)
        st.success("✅ Données actualisées")
    else:
        df = extract_alerts_data()

    if df.empty:
        st.error("❌ Impossible de charger les données")
        return

    if "ligne_complete" not in df.columns:
        st.warning("Structure ancienne détectée, actualisation en cours...")
        df = extract_alerts_data(force_refresh=True)

    df["line_code"] = df["ligne_complete"].apply(extract_line_code_from_text)
    df["icone_ligne"] = df["ligne_complete"].apply(lambda x: get_line_badge_for_streamlit(x, size="medium"))

    selected_modes = st.multiselect("Modes de transport", options=df["mode"].unique(), default=df["mode"].unique())

    filtered_df = df[df["mode"].isin(selected_modes)]

    total_disruptions = len(filtered_df[filtered_df["short_message"].str.len() > 0])
    if total_disruptions > 0:
        st.info(f"📢 {total_disruptions} perturbation(s) en cours")
    else:
        st.success("✅ Aucune perturbation signalée")

    for _, row in filtered_df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 5])

            with col1:
                st.markdown(row["icone_ligne"], unsafe_allow_html=True)

            with col2:
                st.write(f"**{row['ligne_complete']}**")
                if row["enhanced_message"]:
                    severity = get_severity_icon(row["enhanced_message"], row.get("cause"))
                    st.write(f"{severity} {row['enhanced_message']}")

            with col3:
                if row["impacted_object_name"]:
                    st.caption(f"**Arrêts :** {row['impacted_object_name']}")

            st.divider()


if __name__ == "__main__":
    alerts()
