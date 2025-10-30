import json
import os
import time

import requests
import streamlit as st
from core.files import representation_mode_select, display_files
from core.calendar import box_calendar_record
from core.calendar import search_engine as calendar_search_engine
from core.explorer import search_engine as file_search_engine
from utils import generate_badges_html, spacer, toast_for_rerun, get_setting


@st.dialog("🆕 New Chat")
def dialog_new_chat():
    # MARK: New chat
    with st.form("new_chat_form"):
        chat_title = st.text_input(
            "Chat Title",
            placeholder="Enter chat title",
            help="Enter a title for the new chat session.",
        )

        if st.form_submit_button("Create Chat", use_container_width=True):
            response = requests.post(
                "http://back:80/chat/create?title=" + chat_title,
            )
            if response.status_code == 200:
                toast_for_rerun(
                    f"Chat '{chat_title}' created successfully!",
                    icon="🆕",
                )
                load_chat_session(response.json()["id"])
            else:
                st.error("Failed to create chat.")


@st.dialog("📁 Search files", width="large")
def dialog_search_files():
    # MARK: Search files
    with st.expander("Search Files", expanded=True):
        result = file_search_engine(nbr_columns=3)
        if result is not None:
            st.session_state.chat_search_files = result["files"]

    top = st.container()

    if "chat_search_files" in st.session_state:
        representation_mode, show_preview, nbr_of_files_per_line = (
            representation_mode_select(
                default_mode=get_setting("chat_files_default_representation_mode")
            )
        )
        selected = display_files(
            st.session_state.chat_search_files,
            representation_mode=representation_mode,
            show_preview=show_preview,
            nbr_of_files_per_line=nbr_of_files_per_line,
            multi_select_mode=1,
            allow_actions=False,
            key="chat_search_files_selection",
        )
    else:
        selected = []

    with top:
        if st.button("Add Selected Files", disabled=not selected, use_container_width=True):
            for file in selected:
                if file not in st.session_state.chat_files:
                    st.session_state.chat_files.append(file)
            del st.session_state.chat_search_files
            toast_for_rerun(
                f"Added {len(selected)} files to the chat.",
                icon="✅",
            )
            st.rerun()


@st.dialog("📅 Search calendars", width="large")
def dialog_search_calendars():
    # MARK: Search calendars
    result = calendar_search_engine()
    if result:
        st.session_state.chat_search_calendars = result["records"]

    selected = []
    if "chat_search_calendars" in st.session_state:
        default_value = st.checkbox(
            "Select all calendar events",
            label_visibility="hidden",
            value=False,
            key="select_all_calendars",
        )
        spacer()

        for record in st.session_state.chat_search_calendars:
            cols = st.columns([1, 9])
            with cols[0]:
                if st.checkbox("", value=default_value, key=record.get("id")):
                    selected.append(record)
            with cols[1]:
                box_calendar_record(
                    record,
                    show_edit_button=False,
                )

        if st.button("Add Selected Calendar Events", use_container_width=True):
            if len(selected) > 0:
                for record in selected:
                    if record not in st.session_state.chat_calendars:
                        st.session_state.chat_calendars.append(record)
                del st.session_state.chat_search_calendars
                toast_for_rerun(
                    f"Added {len(selected)} calendar events to the chat.",
                    icon="✅",
                )
                st.rerun()
            else:
                st.warning("No calendar events selected.")


@st.dialog("✏️ Edit Chat")
def dialog_edit_chat():
    # MARK: Edit chat
    if "chat_session" not in st.session_state:
        st.warning("No chat session selected.")
        return

    chat_info = st.session_state.chat_infos
    chat_title = st.text_input("Chat Title", value=chat_info["title"])
    chat_description = st.text_area("Chat Description", value=chat_info["description"])

    if st.button("✏️Save Changes", use_container_width=True):
        response = requests.put(
            f"http://back:80/chat/{st.session_state.chat_session}/edit?title={chat_title}&description={chat_description}",
        )
        if response.status_code == 200:
            toast_for_rerun("Chat updated successfully!", icon="✅")
            load_chat_session(st.session_state.chat_session)
        else:
            st.error(f"Failed to update chat. {response.text}")


@st.dialog("🗑️ Delete Chat")
def dialog_delete_chat():
    # MARK: Delete chat
    st.warning(
        "Are you sure you want to delete this chat? This action cannot be undone."
    )
    if st.button(
        "🗑️ Delete Chat",
        use_container_width=True,
        key=f"delete_chat_{st.session_state.chat_session}",
    ):
        response = requests.delete(
            f"http://back:80/chat/{st.session_state.chat_session}",
        )
        if response.status_code == 200:
            toast_for_rerun("Chat deleted successfully!", icon="🗑️")
            clear_chat()
            st.rerun()
        else:
            st.error(f"Failed to delete chat. {response.text}")


@st.dialog("💬 Message presets", width="large")
def dialog_message_presets():
    # MARK: Presets
    def save_presets(presets):
        response = requests.post("http://back:80/settings/chat_presets?value=" + json.dumps(presets))
        if response.status_code == 200:
            toast_for_rerun("Presets saved successfully!", icon="✅")
            st.rerun()
        else:
            st.error(f"Failed to save presets: {response.text}")

    cols = st.columns(4)
    with cols[0]:
        show_message = st.toggle(
            "Show message",
            value=False,
            key="show_message_presets",
        )
    with cols[1]:
        show_edition = st.toggle(
            "Show edition",
            value=False,
            key="show_edition_presets",
        )
    with cols[2]:
        show_deletion = st.toggle(
            "Show deletion",
            value=False,
            key="show_deletion_presets",
        )
    with cols[3]:
        show_addition = st.toggle(
            "Show addition",
            value=False,
            key="show_addition_presets",
        )

    res = requests.get("http://back:80/settings/chat_presets")
    if res.status_code != 200:
        st.error("Failed to load message presets.")
        return
    presets = res.json()

    if len(presets) == 0:
        st.info("No message presets available.")
    else:
        if show_addition:
            with st.form("create_preset"):
                st.subheader("➕ Add new preset")
                new_title = st.text_input("New title")
                new_message = st.text_area("New message")
                submitted = st.form_submit_button("Add preset", use_container_width=True)
                if submitted and new_title and new_message:
                    presets.append([new_title, new_message])
                    save_presets(presets)
                    toast_for_rerun("Preset added successfully!", icon="✅")
                    st.rerun()
            st.divider()

        top = st.container()
        n_cols = 2
        for i in range(len(presets) // n_cols + 1):
            cols = st.columns(n_cols)
            for j in range(n_cols):
                index = i * n_cols + j
                if index < len(presets):
                    preset = presets[index]
                    title, message = preset
                    with cols[j]:
                        with st.container(
                            border=show_message or show_edition or show_deletion
                        ):
                            if st.button(
                                title, use_container_width=True, key=f"preset_{index}"
                            ):
                                send_message(message)
                            if show_message:
                                st.markdown(f"💬 {message}")

                            if show_edition:
                                with st.expander("✏️", expanded=True):
                                    preset[0] = st.text_input(
                                        "Title", value=title, key=f"title_{index}"
                                    )
                                    preset[1] = st.text_area(
                                        "Message", value=message, key=f"msg_{index}"
                                    )

                            if show_deletion:
                                st.divider()
                                if st.button(
                                    "🗑️ Delete",
                                    key=f"delete_{index}",
                                    use_container_width=True,
                                ):
                                    presets.pop(index)
                                    save_presets(presets)
        if show_edition:
            with top:
                if st.button("✏️ Save edition", use_container_width=True, key="save_presets"):
                    save_presets(presets)
                st.divider()

def clear_chat():
    # MARK: Clear
    del st.session_state.chat_session
    del st.session_state.chat_infos
    del st.session_state.chat_files
    del st.session_state.chat_calendars
    del st.session_state.chat_messages


def load_chat_session(session_id, silent: bool = False):
    # MARK: Load
    st.session_state.chat_session = session_id
    st.session_state.chat_infos = requests.get(
        f"http://back:80/chat/{session_id}/info"
    ).json()
    st.session_state.chat_messages = requests.get(
        f"http://back:80/chat/{st.session_state.chat_session}/messages"
    ).json()

    if len(st.session_state.chat_messages) > 0:
        st.session_state.chat_files = st.session_state.chat_messages[-1].get(
            "files", []
        )
        st.session_state.chat_calendars = st.session_state.chat_messages[-1].get(
            "calendar", []
        )
        if not st.session_state.chat_files or len(st.session_state.chat_files) == 0:
            st.session_state.chat_files = []
        else:
            st.session_state.chat_files = json.loads(st.session_state.chat_files)
        if (
            not st.session_state.chat_calendars
            or len(st.session_state.chat_calendars) == 0
        ):
            st.session_state.chat_calendars = []
        else:
            st.session_state.chat_calendars = json.loads(
                st.session_state.chat_calendars
            )
    else:
        st.session_state.chat_files = []
        st.session_state.chat_calendars = []

    if not silent:
        toast_for_rerun(
            f"Loaded chat session: {st.session_state.chat_infos['title']}",
            icon="✅",
        )
    st.rerun()


# MARK: Thinking
def is_chat_running(session_id):
    try:
        response = requests.get(f"http://back:80/chat/{session_id}/is_running")
        if response.status_code == 200:
            return response.json()
        else:
            st.toast("Failed to check chat status.", icon="❌")
            return False
    except requests.RequestException as e:
        st.toast(f"Error checking chat status: {e}", icon="❌")
        return False


def stream_thinking(session_id):
    data = ""
    while True:
        time.sleep(
            0.2 if len(data) == 0 else 0.05
        )  # Adjust sleep time for smoother streaming
        running_info = is_chat_running(session_id)

        if running_info.get("state") == "not_running":
            load_chat_session(session_id, silent=True)

        part_data = running_info.get("answer", "")
        if part_data != data:
            part_data = part_data[len(data) :]
            data += part_data
            yield part_data


def send_message(prompt):
    response = requests.post(
        f"http://back:80/chat/{st.session_state.chat_session}/message",
        json={
            "user_description": get_setting("chat_user_description", "") if st.session_state.chat_include_user_description else "",
            "content": prompt,
            "files": json.dumps(st.session_state.chat_files),
            "calendars": json.dumps(st.session_state.chat_calendars),
        },
    )
    if response.status_code == 200:
        st.session_state.chat_messages.append(response.json())
        st.rerun()
    else:
        st.toast("Failed to send message.", icon="❌")


def chat():
    # MARK: Main
    with st.sidebar:
        with st.container(border=True):
            if st.button("🆕 New Chat", use_container_width=True):
                dialog_new_chat()

            with st.spinner("Loading chat sessions..."):
                # Fetch chat sessions from the backend
                try:
                    chats = requests.get("http://back:80/chat/list").json()
                except requests.RequestException as e:
                    st.error(f"Error fetching chat sessions: {e}")
                    return

            chats = requests.get("http://back:80/chat/list").json()
            selected_session = st.selectbox(
                "Select a session",
                [chat for chat in chats],
                format_func=lambda chat: chat["title"],
                on_change=clear_chat,
            )

    if "chat_session" not in st.session_state and selected_session:
        load_chat_session(selected_session["id"])

    if "chat_session" in st.session_state:
        with st.sidebar:
            # if st.button("🔄 Reload Chat", use_container_width=True):
            #     load_chat_session(st.session_state.chat_session)

            # MARK: Infos
            st.header(f"Chat: {st.session_state.chat_infos['title']}")
            st.markdown(f"**Created on:** {st.session_state.chat_infos['date']}")
            if st.session_state.chat_infos["description"]:
                st.subheader(st.session_state.chat_infos["description"])

            cols = st.columns(2)
            with cols[0]:
                if st.button("✏️ Edit Chat", use_container_width=True):
                    dialog_edit_chat()
            with cols[1]:
                if st.button("🗑️ Delete Chat", use_container_width=True):
                    dialog_delete_chat()

            st.divider()

            if st.button(
                "💬 Message presets", use_container_width=True, key="message_presets"
            ):
                dialog_message_presets()

            st.session_state.chat_include_user_description = st.toggle("Include user description", value=False, key="include_user_description")

            st.markdown("**Files attached**")
            # MARK: Files
            cols = st.columns(2)
            with cols[0]:
                if st.button(
                    "📁 Search",
                    use_container_width=True,
                    key=f"search_files_{st.session_state.chat_session}",
                ):
                    if "chat_search_files" in st.session_state:
                        del st.session_state.chat_search_files
                    dialog_search_files()
            with cols[1]:
                if st.button(
                    "🗑️ Clear",
                    use_container_width=True,
                    key=f"clear_files_{st.session_state.chat_session}",
                ):
                    st.session_state.chat_files = []
                    toast_for_rerun("Cleared all files from the chat.", icon="🗑️")
                    st.rerun()

            if len(st.session_state.chat_files) == 0:
                st.markdown("No files attached to this chat.")
            else:
                st.markdown(
                    generate_badges_html(
                        [
                            "📎 " + os.path.basename(f)
                            for f in st.session_state.chat_files
                        ]
                    ),
                    unsafe_allow_html=True,
                )

            # MARK: Calendars
            st.markdown("**Calendar events attached**")
            cols = st.columns(2)
            with cols[0]:
                if st.button(
                    "📅 Search",
                    use_container_width=True,
                    key=f"search_calendar_{st.session_state.chat_session}",
                ):
                    if "chat_search_calendars" in st.session_state:
                        del st.session_state.chat_search_calendars
                    dialog_search_calendars()
            with cols[1]:
                if st.button(
                    "🗑️ Clear",
                    use_container_width=True,
                    key=f"clear_calendar_{st.session_state.chat_session}",
                ):
                    st.session_state.chat_calendars = []
                    toast_for_rerun("Cleared all calendars events to this chat.")
                    st.rerun()

            if len(st.session_state.chat_calendars) == 0:
                st.markdown("No calendar events attached to this chat.")
            else:
                st.markdown(
                    generate_badges_html(
                        [
                            f"📅 {c['date'].replace('T', ' ').replace('Z', '')} - {c['time_spent']}h - {c['title']}"
                            for c in st.session_state.chat_calendars
                        ],
                        color="rgb(155, 89, 182)",
                        bg_color="rgba(155, 89, 182, 0.2)",
                    ),
                    unsafe_allow_html=True,
                )

        # MARK: Chat
        for message in st.session_state.chat_messages:
            user = message["user"]
            date = message["date"].replace("T", " ").replace("Z", "")
            content = message["content"]
            files = json.loads(message["files"]) if message["files"] else []
            calendars = json.loads(message["calendar"]) if message["calendar"] else []

            with st.chat_message("assistant" if user != "user" else "user"):
                st.caption(f"**{user if user != 'user' else 'You'}** - {date}")
                if user == "user":
                    if len(files) > 0:
                        st.markdown(
                            generate_badges_html(
                                ["📎 " + os.path.basename(f) for f in files]
                            ),
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("No files attached.")
                    if len(calendars) > 0:
                        st.markdown(
                            generate_badges_html(
                                [
                                    f"📅 {c['date'].replace('T', ' ').replace('Z', '')} - {c['time_spent']}h - {c['title']}"
                                    for c in calendars
                                ],
                                color="rgb(255, 200, 255)",
                                bg_color="rgba(155, 89, 182, 0.3)",
                            ),
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("No calendar events attached.")

                    if len(files) > 0 or len(calendars) > 0:
                        spacer(15)
                st.markdown(content)

        if is_chat_running(st.session_state.chat_session).get("state") != "not_running":
            with st.chat_message("assistant"):
                with st.spinner("Thinking...", show_time=True):
                    st.write_stream(stream_thinking(st.session_state.chat_session))

        prompt = st.chat_input(
            "Ask a question.",
        )
        if prompt:
            send_message(prompt)


if __name__ == "__main__":
    chat()
