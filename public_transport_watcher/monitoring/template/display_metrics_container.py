import streamlit as st

def display_metric_container(label, value, percentage=None):
    """Display metric in bordered container with traffic light colors for percentages."""
    
    traffic_lights = [
        (90, "🟢"),
        (70, "🟡"),
        (0, "🔴")
    ]
    
    with st.container(border=True):
        if percentage:
            icon = next(icon for threshold, icon in traffic_lights if percentage >= threshold)
        st.metric(label, f"{icon} {value}" if percentage else value)
