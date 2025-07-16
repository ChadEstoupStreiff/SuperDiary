import json
import os
import time

import requests
import streamlit as st
from core.explorer import search_engine
from utils import toast_for_rerun, generate_badges_html, spacer


@st.dialog("🆕 New Chat")
def dialog_new_chat():
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


@st.dialog("📁 Search files")
def dialog_search_files():
    result = search_engine(nbr_columns=2)
    if result:
        st.session_state.chat_search_files = result["files"]

    selected = []
    if "chat_search_files" in st.session_state:
        default_value = st.checkbox(
            "Select all files",
            label_visibility="hidden",
            value=False,
            key="select_all_files",
        )
        spacer()
        for file in st.session_state.chat_search_files:
            filename = os.path.basename(file)
            if st.checkbox(filename, value=default_value, key=file):
                if file not in selected:
                    selected.append(file)
            else:
                if file in selected:
                    selected.remove(file)

        if st.button("Add Selected Files", use_container_width=True):
            if len(selected) > 0:
                for file in selected:
                    if file not in st.session_state.chat_files:
                        st.session_state.chat_files.append(file)
                del st.session_state.chat_search_files
                toast_for_rerun(
                    f"Added {len(selected)} files to the chat.",
                    icon="✅",
                )
                st.rerun()
            else:
                st.warning("No files selected.")

@st.dialog("✏️ Edit Chat")
def dialog_edit_chat():
    if "chat_session" not in st.session_state:
        st.warning("No chat session selected.")
        return

    chat_info = st.session_state.chat_infos
    chat_title = st.text_input("Chat Title", value=chat_info["title"])
    chat_description = st.text_area("Chat Description", value=chat_info["description"])

    if st.button("Save Changes", use_container_width=True):
        response = requests.put(
            f"http://back:80/chat/{st.session_state.chat_session}/edit?title={chat_title}&description={chat_description}",
        )
        if response.status_code == 200:
            toast_for_rerun("Chat updated successfully!", icon="✅")
            load_chat_session(st.session_state.chat_session)
        else:
            st.error(f"Failed to update chat. {response.text}")

def clear_chat():
    del st.session_state.chat_session
    del st.session_state.chat_infos
    del st.session_state.chat_files
    del st.session_state.chat_messages


def load_chat_session(session_id, silent: bool = False):
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
        if not st.session_state.chat_files or len(st.session_state.chat_files) == 0:
            st.session_state.chat_files = []
        else:
            st.session_state.chat_files = json.loads(st.session_state.chat_files)
    else:
        st.session_state.chat_files = []

    if not silent:
        toast_for_rerun(
            f"Loaded chat session: {st.session_state.chat_infos['title']}",
            icon="✅",
        )
    st.rerun()


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
        time.sleep(0.2)
        running_info = is_chat_running(session_id)
        
        if running_info.get("state") == "not_running":
            load_chat_session(
                session_id, silent=True
            )

        part_data = running_info.get("answer", "")
        if part_data != data:
            part_data = part_data[len(data):]
            data += part_data
            yield part_data

def chat():
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

            st.header(f"Chat: {st.session_state.chat_infos['title']}")
            st.markdown(f"**Created on:** {st.session_state.chat_infos['date']}")
            if st.session_state.chat_infos["description"]:
                st.subheader(st.session_state.chat_infos["description"])

            if st.button("✏️ Edit Chat", use_container_width=True):
                dialog_edit_chat()
            st.divider()

            if st.button("📁 Search for files", use_container_width=True):
                if "chat_search_files" in st.session_state:
                    del st.session_state.chat_search_files
                dialog_search_files()

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

        for message in st.session_state.chat_messages:
            user = message["user"]
            date = message["date"].replace("T", " ").replace("Z", "")
            content = message["content"]
            files = json.loads(message["files"]) if message["files"] else []

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
                        spacer(15)
                    else:
                        st.caption("No files attached.")
                st.markdown(content)

        if is_chat_running(st.session_state.chat_session).get("state") != "not_running":
            with st.chat_message("assistant"):
                with st.spinner("Thinking...", show_time=True):
                    st.write_stream(
                        stream_thinking(st.session_state.chat_session)
                    )

        prompt = st.chat_input(
            "Ask a question.", disabled=len(st.session_state.chat_files) == 0
        )
        if prompt:
            response = requests.post(
                f"http://back:80/chat/{st.session_state.chat_session}/message",
                json={
                    "content": prompt,
                    "files": st.session_state.chat_files
                }
            )
            if response.status_code == 200:
                st.session_state.chat_messages.append(response.json())
                st.rerun()
            else:
                st.toast("Failed to send message.", icon="❌")


if __name__ == "__main__":
    chat()
