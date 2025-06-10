import streamlit as st
from utilities.auth import *

st.set_page_config(layout="wide", page_title="Product Dashboard")

st.title("Income & Expenses")

with st.sidebar:
    if is_logged_in():
        logout_button(key="logout")
    else:
        open_login_page(key="login")

    st.write("---")
