import datetime

import requests
import streamlit as st
from core.calendar import box_calendar_record
from core.files import display_files
from utils import get_setting, refractor_text_area, toast_for_rerun


@st.dialog("🆕 Create Record", width="large")
def dialog_create_record(projects):
    new_record_title = st.text_input(
        "Title",
        placeholder="Enter title",
        help="Enter the title for this record.",
    )

    cols = st.columns(2)
    with cols[0]:
        new_record_project = st.selectbox(
            "Project",
            options=[p["name"] for p in projects],
            index=0,
            help="Select a project for this record.",
        )
    with cols[1]:
        new_record_date = st.date_input("Date")

    cols = st.columns(2)
    with cols[0]:
        new_start_time = st.time_input(
            "Start Time",
            value=None,
            step=datetime.timedelta(minutes=30),
            help="Select the start time for this record.",
        )
    with cols[1]:
        new_record_time_spent = st.number_input(
            "Time Spent (hours)",
            min_value=0.0,
            max_value=24.0,
            value=7.0,
            step=0.1,
            help="Enter the time spent on this record in hours.",
        )

    new_record_description = refractor_text_area("Description", height=100)
    new_record_location = st.text_input(
        "Location",
        placeholder="Enter location (optional)",
        help="Enter the location for this record (optional)",
    )

    new_record_attendees = st.text_input(
        "Attendees",
        placeholder="Enter attendees",
        help="Enter the attendees for this record, separated by commas.",
    )

    if st.button("Save Record", use_container_width=True):
        if len(new_record_title) == 0:
            st.error("Title cannot be empty.")
            return
        request = f"http://back:80/calendar/record?project={new_record_project}&date={new_record_date}&title={new_record_title}&time_spent={new_record_time_spent}"
        if new_record_description:
            request += f"&description={new_record_description}"
        if new_record_location:
            request += f"&location={new_record_location}"
        if new_record_attendees:
            request += f"&attendees={new_record_attendees}"
        if new_start_time:
            request += f"&start_time={new_start_time.strftime('%H:%M:%S')}"
        response = requests.post(request)
        if response.status_code == 200:
            toast_for_rerun(
                "Record created successfully!",
                icon="🆕",
            )
            st.rerun()
        else:
            st.error(f"Error creating record: {response.text}")


def box_date(date):
    files = requests.get(
        f"http://back:80/files/search?start_date={date}&end_date={date}"
    )
    error_files = None
    if files.status_code == 200:
        files = files.json()
    else:
        error_files = files.text
        files = []

    records = requests.get(
        f"http://back:80/calendar/search?start_date={date}&end_date={date}"
    )
    error_records = None
    if records.status_code == 200:
        records = records.json()
    else:
        error_records = records.text
        records = []

    target_hourly_working_time = get_setting("target_hourly_working_time") or 7.5

    def find_emoji_for_time_spent(hours, date):
        if date > datetime.date.today():
            return ""
        elif date == datetime.date.today():
            return "🫡 "
        else:
            if hours == 0:
                return "⚠️ "
            if (
                hours >= target_hourly_working_time - 1
                and hours <= target_hourly_working_time + 1
            ):
                return "✅ "
            elif hours > target_hourly_working_time + 1:
                return "🔥 "
            else:
                return "🛌 "

    with st.expander(
        find_emoji_for_time_spent(sum([r["time_spent"] for r in records]), date)
        + date.strftime("%Y-%m-%d")
        + f" - **{len(records)}** records, **{len(files)}** files, **{sum([r['time_spent'] for r in records])}** hours",
        expanded=False,
    ):
        tabs = st.tabs([f"📅 Records: {len(records)}", f"📁 Files: {len(files)}"])
        with tabs[0]:
            st.error(
                f"Error fetching records: {error_records}"
            ) if error_records else None
            if records:
                for record in records:
                    box_calendar_record(record, show_date=False)
            else:
                st.info("No records found for this date.")
        with tabs[1]:
            st.error(f"Error fetching files: {error_files}") if error_files else None
            if files:
                display_files(
                    files,
                    representation_mode=0,
                    multi_select_mode=0,
                    show_preview=False,
                    key=f"files_for_date_{date}",
                )
            else:
                st.info("No files found for this date.")


def calendar():
    projects = requests.get("http://back:80/projects").json()

    with st.sidebar:
        if st.button("🆕 Create Record", use_container_width=True):
            dialog_create_record(projects)
        enable_weekends = st.toggle("Enable Weekends", value=False)
        cols = st.columns(2)
        with cols[0]:
            selected_month = st.selectbox(
                "Month",
                options=range(12),
                format_func=lambda x: [
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December",
                ][x],
                index=datetime.datetime.now().month - 1,
            )
        with cols[1]:
            selected_year = st.number_input(
                "Year",
                min_value=0,
                max_value=5000,
                value=datetime.datetime.now().year,
                step=1,
            )

    cols = st.columns(7 if enable_weekends else 5)
    for i in range(7 if enable_weekends else 5):
        with cols[i]:
            st.write(
                f"""### **{
                    [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday",
                    ][i]
                }**"""
            )
    start_date = datetime.date(selected_year, selected_month + 1, 1)
    start_date_offset = start_date.weekday()
    for i in range(6):
        cols = st.columns(7 if enable_weekends else 5)
        for j in range(7 if enable_weekends else 5):
            if i * 7 + j >= start_date_offset:
                date = start_date + datetime.timedelta(
                    days=i * 7 + j - start_date_offset
                )
                if date.month == selected_month + 1:
                    with cols[j]:
                        box_date(date)


if __name__ == "__main__":
    calendar()
