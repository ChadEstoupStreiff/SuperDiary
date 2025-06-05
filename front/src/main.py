import streamlit as st

from views.dashboard import dashboard
from views.explorer import explorer

if __name__ == "__main__":
    st.set_page_config(
        page_title="Super Diary",
        page_icon=":rocket:",
        layout="wide",
    )

    pg = st.navigation(
        [
            st.Page(
                dashboard,
                title="Dashboard",
                icon="🏠",
            ),
            st.Page(
                explorer,
                title="Explorer",
                icon="🔍",
            ),
        ]
    )
    pg.run()
