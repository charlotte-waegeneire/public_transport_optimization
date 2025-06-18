import re

import bcrypt
import streamlit as st

from public_transport_watcher.db.models.user import User
from public_transport_watcher.utils import get_db_session


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    if isinstance(hashed, str):
        return hashed
    return hashed.decode("utf-8")


def create_new_user():
    st.title("Create New User")

    if "user_created" in st.session_state and st.session_state.user_created:
        st.success("User created successfully!")
        st.session_state.user_created = False

    with st.form("user_creation_form"):
        user = st.text_input("Username", help="Username must be at least 3 characters")
        email = st.text_input("Email", help="Please enter a valid email address")
        password = st.text_input("Password", type="password", help="Password must be at least 8 characters")
        submit_button = st.form_submit_button("Create User")

        if submit_button:
            errors = []

            if not user or len(user) < 3:
                errors.append("Username must be at least 3 characters")

            email_pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
            if not email or not email_pattern.match(email):
                errors.append("Please enter a valid email address")

            if not password or len(password) < 8:
                errors.append("Password must be at least 8 characters")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                hashed_password = hash_password(password)
                session = get_db_session()
                try:
                    existing_user = session.query(User).filter((User.username == user) | (User.email == email)).first()

                    if existing_user:
                        if existing_user.username == user:
                            st.error(f"Username '{user}' already exists")
                        else:
                            st.error(f"Email '{email}' already registered")
                    else:
                        user_obj = User(username=user, email=email, password_hash=hashed_password)
                        session.add(user_obj)
                        session.commit()
                        st.success(f"User created: {user_obj}")
                        st.session_state.user_created = True
                        st.rerun()
                except Exception as e:
                    session.rollback()
                    st.error(f"Error creating user: {e}")
                finally:
                    session.close()
