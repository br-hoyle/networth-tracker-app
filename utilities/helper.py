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
