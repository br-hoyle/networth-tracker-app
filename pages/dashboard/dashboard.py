import streamlit as st
from utilities.auth import *
from streamlit_gsheets import GSheetsConnection

from utilities.sidebar import show_app_sidebar
from utilities.helper import *
from utilities.gsheets import *
from utilities.calculations import *

from pages.dashboard.components.spreadsheet import *

from pages.dashboard.components.networth import networth_tile
from pages.dashboard.components.target_networth import target_networth_tile
from pages.dashboard.components.fire_networth import financial_independence_tile
from pages.dashboard.components.investments_to_assets import investments_to_assets_tile
from pages.dashboard.components.retirement_margin import retirement_margin_tile
from pages.dashboard.components.balance_by_group import balance_by_group_tile
from pages.dashboard.components.balance_by_institution import (
    balance_by_institution_over_time_tile,
)

from utilities.helper import *


# ----------------- HEADER ----------------- #
st.set_page_config(layout="wide", page_title="Product Dashboard")

view_type = show_app_sidebar()

# Initialize Connection & Check for Staleness
conn = st.connection("gsheets", type=GSheetsConnection)
load_settings_to_session_state(conn=conn)

header_cols = st.columns([7, 1, 1])
with header_cols[0]:
    st.title("Networth Dashboard")
with header_cols[1]:
    st.write("")
    st.write("")
    refresh_connection()
with header_cols[2]:
    st.write("")
    st.write("")
    if st.button("☰ Settings", type="secondary", use_container_width=True):
        settings_assumptions(conn=conn)

check_balance_staleness(conn)

## ----------- BALANCES DASHBOARD ----------- ##
if view_type == "Dashboard":

    row_one_columns = st.columns([4, 3, 3])

    # NETWORTH OVER TIME
    with row_one_columns[0]:
        networth_tile(conn=conn)

    # SUPPORTING NETWORTH MEASURES
    with row_one_columns[1]:

        ## TARGET NETWORTH
        target_networth_tile(conn=conn)

        ## INVESTMENTS TO ASSETS
        investments_to_assets_tile(conn=conn)

    with row_one_columns[2]:

        ## FINANCIAL INDEPENDENCE TRACK
        financial_independence_tile(conn=conn)

        ## RETIREMENT MARGIN
        retirement_margin_tile(conn=conn)

    # BALANCE BY GROUP
    balance_by_group_tile(conn=conn)

    # BALANCE BY CATEGORY OVER TIME
    balance_by_institution_over_time_tile(conn=conn)
    st.write("hello")


## ---------- BALANCES SPREADSHEET ---------- ##
elif view_type == "Spreadsheet":

    balances_spreadsheet(conn=conn)

render_footer()
