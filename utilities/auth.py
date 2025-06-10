import streamlit as st
import time


def open_login_page(key):
    st.button("Login", on_click=show_login_form, key=key, type="primary")


def show_login_form():
    @st.dialog("Login")
    def login_form():
        username = st.text_input("Enter Username:", type="default")
        password = st.text_input("Enter Password:", type="password")

        if st.button("Log In", type="primary"):
            if login_user(username, password):
                st.success("Login successful! Use the sidebar to access your data.")
                time.sleep(0.25)
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")

    login_form()


def login_user(username: str, password: str) -> bool:
    expected_user = st.secrets["user"].get("APP_USERNAME", "")
    expected_pass = st.secrets["user"].get("APP_PASSWORD", "")

    if username == expected_user and password == expected_pass:
        st.session_state["logged_in"] = True
        return True
    return False


def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


def logout_user():
    st.session_state["logged_in"] = False


def logout_button(key):
    if is_logged_in():
        if st.button("Logout", key=key):
            logout_user()
            st.success("You have been logged out.")
            st.rerun()
    else:
        open_login_page(key="logout")
