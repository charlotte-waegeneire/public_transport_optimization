import streamlit as st


def display_metric_container(label, value):
    """Display metric in bordered container."""
    with st.container(border=True):
        st.metric(label, value)
