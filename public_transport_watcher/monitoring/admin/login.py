import bcrypt
import streamlit as st

from public_transport_watcher.db.models.user import User
from public_transport_watcher.utils import get_db_session


def check_password_hash(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8") if isinstance(hashed_password, str) else hashed_password
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


def check_user_password(username: str, password: str) -> tuple:
    try:
        db_session = get_db_session()

        user = db_session.query(User).filter_by(username=username).first()

        if not user:
            return False, None

        is_valid = check_password_hash(password, user.password_hash)
        if not is_valid:
            return False, None
        return True, user.id
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return False, None
    finally:
        db_session.close()


def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        is_valid, user_id = check_user_password(username, password)
        if is_valid:
            st.success("Login successful")
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = user_id
            st.session_state["username"] = username
            st.rerun()
        else:
            st.error("Invalid username or password")
