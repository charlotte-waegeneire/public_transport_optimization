import time
import streamlit as st

from public_transport_watcher.utils import get_query_result


def get_safe_query_execution(query_name, description="Requête"):
    """Executes a query safely with loading indicator."""

    try:
        start_time = time.time()
        loading_placeholder = st.empty()
        loading_placeholder.caption(f"🔄 Chargement {description}...")

        result = get_query_result(query_name)

        end_time = time.time()
        execution_time = end_time - start_time

        loading_placeholder.caption(f"✅ {description} chargé en {execution_time:.2f}s")
        return result

    except Exception as e:
        loading_placeholder.error(f"❌ Erreur: {str(e)}")
        return None
