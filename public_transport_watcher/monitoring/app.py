import streamlit as st

from public_transport_watcher.monitoring.admin import create_new_user, login, show_users
from public_transport_watcher.monitoring.api_use import journey_search
from public_transport_watcher.monitoring.reports import alerts, dashboard

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

login_page = st.Page(login, title="Login", icon=":material/login:")

create_new_user_page = st.Page(create_new_user, title="Create New User", icon=":material/person_add:")
show_users_page = st.Page(show_users, title="Users", icon=":material/person:")

alerts_page = st.Page(alerts, title="Alerts", icon=":material/notification_important:")
dashboard_page = st.Page(dashboard, title="Dashboard", icon=":material/dashboard:")

journeys_page = st.Page(journey_search, title="Travelers statistics", icon=":material/search:")

if st.session_state.logged_in:
    pg = st.navigation(
        {
            "Dashboard": [dashboard_page, alerts_page],
            "API Use": [journeys_page],
            "Admin": [create_new_user_page, show_users_page],
        }
    )
else:
    pg = st.navigation([login_page])


pg.run()
