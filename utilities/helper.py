import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pandas as pd
from pathlib import Path
import toml


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
        st.success(
            f"✅ Balance **last updated {days_old} days ago** ({latest_date.strftime('%m/%d/%Y')})."
        )


def check_transactions_staleness(conn: GSheetsConnection):
    """Return banner indicating staleness of transaction data."""

    # Query latest balance date from the records worksheet
    result = conn.query(
        "SELECT MAX(STRPTIME(full_date, '%m/%d/%Y')) AS max_date FROM transactions;"
    )

    max_full_date = result.iloc[0, 0]

    if max_full_date is None:
        st.error("No transaction records found. Please enter transaction data.")
        return

    # Convert to date for comparison
    latest_date = pd.to_datetime(max_full_date).date()
    today = datetime.today().date()
    days_old = (today - latest_date).days

    # Show appropriate banner
    if days_old > 45:
        st.error(
            f"🚨 Last recorded transactions **{days_old} days ago** ({latest_date.strftime('%m/%d/%Y')}). Please update transaction records."
        )
    elif days_old > 30:
        st.warning(
            f"⚠️ Last recorded transactions **{days_old} days ago** ({latest_date.strftime('%m/%d/%Y')})."
        )
    else:
        st.success(
            f"✅ Last recorded transactions **{days_old} days ago** ({latest_date.strftime('%m/%d/%Y')})."
        )


def get_config_value(dot_path: str, config_path: str = ".streamlit/config.toml"):
    """
    Loads a TOML config file and retrieves a nested value based on a dot-separated path.

    Parameters
    - dot_path (str): Dot-separated string representing the key path (e.g., "theme.ColorPalette.green")
    - config_path (str): Path to the TOML file (default is ".streamlit/config.toml")

    Returns
    - The retrieved value, or None if any key in the chain does not exist.
    """
    # Load the TOML config file
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found at: {config_path}")

    config = toml.load(config_file)

    # Traverse the config using chained .get()
    keys = dot_path.split(".")
    current = config
    for key in keys:
        current = current.get(key)
        if current is None:
            return None  # Key not found, exit early

    return current


def render_footer():
    st.markdown(
        """
    <hr style="margin-top: 3rem;" />
    <div style='text-align: center; padding: 1rem; color: gray; font-size: 1rem;'>
        Built with 
        <img src="https://image.pngaaa.com/798/5084798-middle.png" style="height: 1em; vertical-align: middle;" alt="Streamlit logo"> 
        <a href="https://streamlit.io/" target="_blank" style="color: gray; text-decoration: none;">Streamlit</a>
        and 
        <img src="https://upload.wikimedia.org/wikipedia/commons/3/30/Google_Sheets_logo_%282014-2020%29.svg" style="height: 1em; vertical-align: middle;" alt="Google Sheets logo">
        Google Sheets
        <br />
        © 2025 Benjamin Hoyle
    </div>
            """,
        unsafe_allow_html=True,
    )
