import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pandas as pd


@st.cache_data
def convert_for_download(df):
    return df.to_csv().encode("utf-8")


def check_balance_staleness(conn: GSheetsConnection):
    """Return banner indicating staleness of balance data."""

    # Query latest balance date from the balances worksheet
    result = conn.query(
        "SELECT MAX(STRPTIME(full_date, '%m/%d/%Y')) AS max_date FROM balances;"
    )

    max_full_date = result.iloc[0, 0]

    if max_full_date is None:
        st.error("No balance records found. Please enter balance data.")
        return

    # Convert to date for comparison
    latest_date = pd.to_datetime(max_full_date).date()
    today = datetime.today().date()
    days_old = (today - latest_date).days

    # Show appropriate banner
    if days_old > 14:
        st.error(
            f"🚨 Balance **last updated {days_old} days ago** ({latest_date.strftime('%m/%d/%Y')}). Please update account balances."
        )
    elif days_old > 7:
        st.warning(
            f"⚠️ Balance **last updated {days_old} days ago** ({latest_date.strftime('%m/%d/%Y')})."
        )
    else:
        st.toast(
            f"✅ Balance data is up to date as of {latest_date.strftime('%m/%d/%Y')})."
        )
