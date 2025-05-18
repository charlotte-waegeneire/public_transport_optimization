import streamlit as st

from public_transport_watcher.db.models.user import User
from public_transport_watcher.utils import get_db_session


def _get_users():
    db_session = get_db_session()
    users = db_session.query(User).all()
    return users


def _delete_user(user_id: int):
    db_session = get_db_session()
    user = db_session.query(User).filter_by(id=user_id).first()
    if user:
        db_session.delete(user)
        db_session.commit()
        return True


def show_users():
    st.header("User management", divider="blue")

    # Add search functionality
    search_query = st.text_input("🔍 Search for a user", placeholder="Enter a username...")

    users = _get_users()

    # Filter users based on search query
    if search_query:
        users = [user for user in users if search_query.lower() in user.username.lower()]

    # Display user count
    st.caption(f"{len(users)} users found")

    user_container = st.container()

    if not users:
        user_container.info("No users found.")
    else:
        # Create columns for better layout
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.subheader("Username")
        with col2:
            st.subheader("Email")
        with col3:
            st.subheader("Action")

        st.divider()

        # Display users in a more structured way
        for user in users:
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                is_current_user = st.session_state.get("user_id") == user.id
                if is_current_user:
                    st.markdown(f"**{user.username}** (you)")
                else:
                    st.markdown(f"{user.username}")

            with col2:
                st.markdown(f"{user.email}")

            with col3:
                if st.session_state.get("user_id") != user.id:
                    if st.button("🗑️ Delete", key=f"delete_{user.id}", type="primary", use_container_width=True):
                        if _delete_user(user.id):
                            st.success(f"User '{user.username}' deleted successfully!")
                            st.rerun()
                else:
                    st.markdown("*Current user*")

            st.divider()

    # Add a button to refresh the list
    if st.button("🔄 Refresh list", type="secondary"):
        st.rerun()
