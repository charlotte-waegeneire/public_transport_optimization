import streamlit as st
import pandas as pd
from datetime import datetime
import time

from public_transport_watcher.extractor.extract import extract_traffic_data

def get_status_color(status):
    status_colors = {
        'onTime': '🟢',
        'delayed': '🟠',
        'cancelled': '🔴',
        'early': '🟢',
        'departed': '🟡',
        'unknown': '⚪',
        'Inconnu': '⚪'
    }
    return status_colors.get(status, '⚪')

def get_status_text(status):
    status_text = {
        'onTime': 'À l\'heure',
        'delayed': 'Retardé',
        'cancelled': 'Annulé',
        'early': 'En avance',
        'departed': 'Parti',
        'unknown': 'Inconnu',
        'Inconnu': 'Inconnu'
    }
    return status_text.get(status, 'Inconnu')


def alerts():
    st.title("🚇 État du Trafic - Transports Île-de-France")

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Actualiser"):
            st.rerun()

    with col2:
        st.write(f"*Dernière mise à jour : {datetime.now().strftime('%H:%M:%S')}*")

    with st.spinner('Chargement des données de trafic...'):
        try:
            traffic_df = extract_traffic_data()

            if traffic_df.empty:
                st.warning("⚠️ Aucune donnée de trafic disponible pour le moment.")
                return

            # Remplacer les NaN dans network_name pour éviter les problèmes d'affichage
            traffic_df['network_name'] = traffic_df['network_name'].fillna('RATP')

            st.sidebar.header("🔍 Filtres")

            # Filtre par type de transport uniquement
            transport_modes = traffic_df['transport_mode'].unique() if 'transport_mode' in traffic_df.columns else []
            selected_modes = st.sidebar.multiselect(
                "Type de transport",
                options=transport_modes,
                default=transport_modes
            )

            # Application du filtre transport mode uniquement
            filtered_df = traffic_df.copy()
            if selected_modes and 'transport_mode' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['transport_mode'].isin(selected_modes)]

            if not filtered_df.empty:
                status_priority = {'cancelled': 4, 'delayed': 3, 'departed': 2, 'early': 1, 'onTime': 1, 'unknown': 0, 'Inconnu': 0}

                line_status = filtered_df.groupby(['line_name', 'full_line_name', 'network_name']).agg({
                    'statut': lambda x: max(x, key=lambda s: status_priority.get(s, 0)),
                    'destination': 'count'
                }).reset_index()

                line_status.rename(columns={'destination': 'nb_destinations'}, inplace=True)
                line_status = line_status.sort_values(['network_name', 'line_name'])

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📊 Lignes surveillées", len(line_status))
                with col2:
                    normal_count = len(line_status[line_status['statut'].isin(['onTime', 'early'])])
                    st.metric("🟢 Lignes normales", normal_count)
                with col3:
                    delayed_count = len(line_status[line_status['statut'] == 'delayed'])
                    st.metric("🟠 Lignes retardées", delayed_count)
                with col4:
                    cancelled_count = len(line_status[line_status['statut'] == 'cancelled'])
                    st.metric("🔴 Lignes perturbées", cancelled_count)

                st.markdown("---")

                current_network = None
                for _, row in line_status.iterrows():
                    if current_network != row['network_name']:
                        current_network = row['network_name']
                        st.subheader(f"🚉 {current_network}")

                    col1, col2, col3, col4 = st.columns([1, 3, 2, 1])

                    with col1:
                        st.markdown(f"### {get_status_color(row['statut'])}")

                    with col2:
                        line_display = row['full_line_name'] if pd.notna(row['full_line_name']) else row['line_name']
                        st.markdown(f"**{line_display}**")

                    with col3:
                        st.markdown(f"*{get_status_text(row['statut'])}*")

                    with col4:
                        st.markdown(f"📍 {row['nb_destinations']}")

                st.markdown("---")
                st.markdown("### 📖 Légende")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("🟢 **Normal** - Service à l'heure")
                    st.markdown("🟠 **Retardé** - Retards signalés")
                with col2:
                    st.markdown("🔴 **Perturbé** - Service annulé/interrompu")
                    st.markdown("⚪ **Inconnu** - Statut non disponible")

            else:
                st.info("🔍 Aucune ligne ne correspond aux filtres sélectionnés.")

        except Exception as e:
            st.error(f"❌ Erreur lors du chargement des données : {str(e)}")
            st.info("💡 Vérifiez que votre clé API est configurée et que le service est accessible.")
if __name__ == "__main__":
    alerts()