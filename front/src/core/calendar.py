import datetime

import requests
import streamlit as st
from utils import generate_project_visual_markdown


def box_calendar_record(record, show_project: bool = True, show_date: bool = True):
    """
    Display a calendar record in a box format.
    """
    with st.container(border=True):
        project = record.get("project", [])
        date = (
            datetime.datetime.strptime(record["date"], "%Y-%m-%dT%H:%M:%S")
            if "date" in record
            else datetime.date.today()
        )
        title = record.get("title", "No Title")
        description = record.get("description", None)
        time_spent = record.get("time_spent", 0)
        location = record.get("location", None)
        attendees = record.get("attendees", None)

        if show_project:
            project = requests.get(f"http://back:80/project/{project}")
            if project.status_code == 200:
                project = project.json()
            else:
                project = {"name": "Unknown Project", "color": "#FFFFFF"}

        st.markdown(f"### {title}")
        if show_project:
            st.markdown(
                f"**📌 Project:** {generate_project_visual_markdown(project['name'], project['color'])}",
                unsafe_allow_html=True,
            )
        if show_date:
            st.markdown(f"**📅 Date:** {date.strftime('%Y-%m-%d')}")
        st.markdown(f"**⏱️ Time Spent:** {time_spent} hours")

        if location:
            st.markdown(f"**📍 Location:** {location}")
        if attendees:
            st.markdown(f"**👥 Attendees:** {attendees}")
        if description:
            st.markdown("**🗒️ Description:**")
            with st.container(border=True):
                st.markdown(description)
