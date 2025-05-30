import streamlit as st


def display_metric_container(label, value, percentage=None):
    """Display metric in bordered container with traffic light colors for percentages."""

    with st.container(border=True):
        if percentage is not None:
            if percentage >= 90:
                icon = "🟢"
            elif percentage >= 70:
                icon = "🟡"
            else:
                icon = "🔴"

            st.metric(label, f"{icon} {value}")

        else:
            st.metric(label, value)
