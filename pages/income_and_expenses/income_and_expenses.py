import streamlit as st
from streamlit_gsheets import GSheetsConnection

from utilities.sidebar import show_app_sidebar
from utilities.gsheets import (
    refresh_connection,
    load_settings_to_session_state,
    settings_assumptions,
)

from pages.income_and_expenses.components.spreadsheet import transactions_spreadsheet

from utilities.helper import *

st.set_page_config(layout="wide", page_title="Income & Expenses")

view_type = show_app_sidebar()

# Initialize Connection & Check for Staleness
conn = st.connection("gsheets", type=GSheetsConnection)
load_settings_to_session_state(conn=conn)

header_cols = st.columns([7, 1, 1])
with header_cols[0]:
    st.title("Income & Expenses")
with header_cols[1]:
    st.write("")
    st.write("")
    refresh_connection()
with header_cols[2]:
    st.write("")
    st.write("")
    if st.button("☰ Settings", type="secondary", use_container_width=True):
        settings_assumptions(conn=conn)

check_transactions_staleness(conn)

if view_type == "Dashboard":
    st.warning("This page is under construction.", icon="⚠️")

if view_type == "Spreadsheet":
    transactions_spreadsheet(conn)


render_footer()
