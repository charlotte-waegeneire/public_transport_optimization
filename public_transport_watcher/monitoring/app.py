import streamlit as st

from public_transport_watcher.monitoring.admin import create_new_user, login, show_users
from public_transport_watcher.monitoring.api_use import journey_search, dashboard_api
from public_transport_watcher.monitoring.reports import alerts, dashboard

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

login_page = st.Page(login, title="Connexion", icon=":material/login:")

create_new_user_page = st.Page(create_new_user, title="Créer un utilisateur", icon=":material/person_add:")
show_users_page = st.Page(show_users, title="Utilisateurs", icon=":material/person:")

alerts_page = st.Page(alerts, title="Alertes", icon=":material/notification_important:")
dashboard_page = st.Page(dashboard, title="Utilisation des transports publics", icon=":material/dashboard:")

dashboard_api_page = st.Page(dashboard_api, title="Monitoring de l'API", icon=":material/dashboard:")
journeys_page = st.Page(journey_search, title="Statistiques des recherches API", icon=":material/search:")

if st.session_state.logged_in:
    pg = st.navigation(
        {
            "Transports publics": [dashboard_page, alerts_page],
            "Analyse de l'API": [dashboard_api_page, journeys_page],
            "Administration": [create_new_user_page, show_users_page],
        }
    )
else:
    pg = st.navigation([login_page])

pg.run()
