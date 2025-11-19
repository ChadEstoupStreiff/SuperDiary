import json
from typing import Any, Dict

import pandas
import requests
import streamlit as st
from core.explorer import generate_query_description, search_engine
from core.stateoftheart import (
    format_APA,
    format_BibTeX,
    format_Vancouver,
    get_reference_from_title,
)
from stqdm import stqdm
from utils import toast_for_rerun


def create_table_line(
    file: str, select_default_value: bool, display_projects: bool, display_tags: bool
) -> Dict[str, Any]:
    file_name = file.split("/")[-1]
    file_date = file.split("/")[2]
    stockpile_info = requests.get(
        f"http://back:80/stockpile/get/sota_info_{file_date}_{file_name}"
    )
    if stockpile_info.status_code == 200:
        try:
            info = json.loads(stockpile_info.json())
        except Exception:
            info = {}
    else:
        info = {}
    return {
        "select": select_default_value,
        "Filename": file.split("/")[-1],
        "Upload Date": file.split("/")[2],
        **(
            {
                "Projects": [
                    p["name"]
                    for p in requests.get(f"http://back:80/projects_of/{file}").json()
                ]
            }
            if display_projects
            else {}
        ),
        **(
            {
                "Tags": [
                    t["name"]
                    for t in requests.get(f"http://back:80/tags_of/{file}").json()
                ]
            }
            if display_tags
            else {}
        ),
        **info,
    }


def stateoftheart():
    tags = requests.get("http://back:80/tags").json()
    tags_name = [x["name"] for x in tags]
    sota_tag = requests.get("http://back:80/stockpile/get/sota_tag")

    if sota_tag.status_code != 200:
        sota_tag = None
    else:
        sota_tag = sota_tag.json()

    def update_sota_tag():
        selected_tag = st.session_state.sota_tag_selection
        if selected_tag is not None:
            requests.post(
                f"http://back:80/stockpile/set/sota_tag?value={selected_tag}",
            )
        else:
            requests.delete("http://back:80/stockpile/delete/sota_tag")
        toast_for_rerun("SOTA tag updated.", "✅")

    st.sidebar.selectbox(
        "SOTA Tag",
        options=tags_name,
        on_change=update_sota_tag,
        index=None
        if sota_tag is None or sota_tag not in tags_name
        else tags_name.index(sota_tag),
        key="sota_tag_selection",
        help="Select the tag corresponding to the State-of-the-art files.",
    )

    if sota_tag is None:
        st.warning("Please select a tag for State-of-the-art files.")
    else:
        search_result = search_engine(force_tags=[sota_tag])
        if search_result is not None:
            st.session_state.sota_files = search_result

        if "sota_files" in st.session_state:
            query_str = generate_query_description(st.session_state.sota_files)
            st.caption(query_str)

            if len(st.session_state.sota_files["files"]) == 0:
                st.write("No files found in the system.")
            else:
                with st.sidebar:
                    select_default_value = st.toggle(
                        "Select all by default",
                        value=True,
                        help="If enabled, all files will be selected by default in the table below.",
                    )
                    display_projects = st.toggle(
                        "Display projects",
                        value=False,
                        help="If enabled, the projects associated with each file will be displayed.",
                    )
                    display_tags = st.toggle(
                        "Display tags",
                        value=False,
                        help="If enabled, the tags associated with each file will be displayed.",
                    )
                files = st.session_state.sota_files["files"]
                data_table = pandas.DataFrame.from_dict(
                    [
                        create_table_line(
                            f, select_default_value, display_projects, display_tags
                        )
                        for f in files
                    ]
                )

                table = st.data_editor(
                    data_table,
                    column_config={
                        "select": st.column_config.CheckboxColumn(
                            "select",
                            width="small",
                            default=select_default_value,
                        ),
                        "url": st.column_config.LinkColumn(
                            "URL",
                            width="small",
                            help="Link to the publication.",
                        ),
                        # "Upload Date": st.column_config.DateColumn(
                        #     "Upload Date",
                        #     width="small",
                        #     format="YYYY-MM-DD",
                        # ),
                        # "authors": st.column_config.TextColumn(
                        #     "Authors",
                        #     width="medium",
                        # ),
                        "year": st.column_config.NumberColumn(
                            "Year",
                            width="small",
                        ),
                    },
                    use_container_width=True,
                    hide_index=True,
                    disabled=[
                        "Filename",
                        "Upload Date",
                        "Projects",
                        "Tags",
                    ],
                )

                row_update = False
                for i in range(len(table)):
                    base_dict = {
                        k: v
                        for k, v in data_table.iloc[i].to_dict().items()
                        if k
                        not in ["select", "Filename", "Upload Date", "Projects", "Tags"]
                    }
                    row_dict = {
                        k: v
                        for k, v in table.iloc[i].to_dict().items()
                        if k
                        not in ["select", "Filename", "Upload Date", "Projects", "Tags"]
                    }

                    if base_dict != row_dict:
                        st.info(f"Row {i + 1} has been modified. Saving changes...")
                        row_update = True
                        file = files[i]
                        file_name = file.split("/")[-1]
                        file_date = file.split("/")[2]
                        file_key = f"{file_date}_{file_name}"

                        result = requests.post(
                            f"http://back:80/stockpile/set/sota_info_{file_key}?value={json.dumps(row_dict)}",
                        )
                        if result.status_code != 200:
                            st.error(f"Error while saving SOTA info for file {file}.")
                            st.stop()

                if row_update:
                    toast_for_rerun("SOTA updated.", "✅")
                    st.rerun()

                selected = table.query("select == True")
                st.caption(f"{len(selected)} files selected.")

                selected = [
                    {k: selected[k][i] for k in selected.columns}
                    for i in selected.index
                ]

                cols = st.columns(4)
                with cols[0]:
                    button_search = st.button(
                        "🔍 Find info", use_container_width=True, disabled=not selected
                    )
                with cols[1]:
                    button_format_apa = st.button(
                        "📚 Format APA", use_container_width=True, disabled=not selected
                    )
                with cols[2]:
                    button_format_vancouver = st.button(
                        "📚 Format Vancouver",
                        use_container_width=True,
                        disabled=not selected,
                    )
                with cols[3]:
                    button_format_bibtex = st.button(
                        "📚 Format BibTeX",
                        use_container_width=True,
                        disabled=not selected,
                    )

                if button_search:
                    for file in stqdm(selected, desc="Fetching SOTA info"):
                        file_name = file["Filename"]
                        file_date = file["Upload Date"]
                        file_key = f"{file_date}_{file_name}"
                        founded = get_reference_from_title(file_name)
                        if founded is not None:
                            result = requests.post(
                                f"http://back:80/stockpile/set/sota_info_{file_key}?value={json.dumps(founded)}",
                            )
                            if result.status_code != 200:
                                st.toast(
                                    f"Error while saving SOTA info for file {file}.",
                                    icon="⚠️",
                                )

                    toast_for_rerun("SOTA info updated.", "✅")
                    st.rerun()
                if button_format_apa:
                    st.code(format_APA(selected))
                if button_format_vancouver:
                    st.code(format_Vancouver(selected))
                if button_format_bibtex:
                    st.code(format_BibTeX(selected))
        else:
            st.info("Search for files first :)")


if __name__ == "__main__":
    stateoftheart()
