import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import date, datetime
import pandas as pd
import streamlit as st
from typing import Any


def load_worksheet(conn: GSheetsConnection, worksheet: str) -> pd.DataFrame:
    return conn.read(worksheet=worksheet)


def write_worksheet(conn: GSheetsConnection, worksheet: str, df: pd.DataFrame):
    conn.update(worksheet=worksheet, data=df)


def refresh_connection() -> GSheetsConnection:
    if st.button("Refresh Data", type="secondary", use_container_width=True):
        st.cache_data.clear()


def load_settings_to_session_state(conn: GSheetsConnection):
    df = load_worksheet(conn=conn, worksheet="settings")
    df["value"] = df["value"].astype(str).str.strip()

    def get_scalar(metric: str, cast_type: Any):
        try:
            raw_val = df.loc[df["metric"] == metric, "value"].iloc[0]
            return cast_type(raw_val)
        except (IndexError, ValueError, TypeError):
            return None

    settings = {
        "inflation_rate": float,
        "target_savings_rate": float,
        "target_return_on_investment": float,
        "target_retirement_age": int,
        "replacement_income_rate": float,
    }

    for key, cast in settings.items():
        if key not in st.session_state:
            st.session_state[key] = get_scalar(key, cast)

    if "birthdate" not in st.session_state:
        try:
            birth_val = df.loc[df["metric"] == "birthdate", "value"].iloc[0]
            st.session_state["birthdate"] = pd.to_datetime(birth_val)
        except (IndexError, ValueError, TypeError):
            st.session_state["birthdate"] = None


@st.dialog("Setting")
def settings_assumptions(conn: GSheetsConnection):
    df = load_worksheet(conn=conn, worksheet="settings")
    df["value"] = df["value"].astype(str).str.strip()

    # Exclude birthdate from settings inputs
    editable_df = df[df["metric"] != "birthdate"].copy()

    # Input widgets for all editable metrics
    input_values = {}
    with st.form("settings_assumptions_form"):
        for _, row in editable_df.iterrows():
            metric = row["metric"]
            val = row["value"]

            # Auto-cast known types for better UX
            if metric in {
                "inflation_rate",
                "target_savings_rate",
                "target_return_on_investment",
                "replacement_income_rate",
            }:
                val = float(val)
                input_values[metric] = st.number_input(
                    label=metric.replace("_", " ").title(),
                    value=val,
                    step=0.01,
                    min_value=0.0,
                    key=metric,
                )
            elif metric == "target_retirement_age":
                val = int(val)
                input_values[metric] = st.number_input(
                    label="Retirement Age",
                    value=val,
                    step=1,
                    min_value=0,
                    max_value=100,
                    key=metric,
                )
            else:
                input_values[metric] = st.text_input(
                    label=metric.replace("_", " ").title(), value=val, key=metric
                )

        if st.form_submit_button("Save", use_container_width=True):
            # Update the DataFrame with new values
            for metric, new_value in input_values.items():
                df.loc[df["metric"] == metric, "value"] = str(new_value)

            # Re-write the full DataFrame including unchanged birthdate
            conn.update(worksheet="settings", data=df)
            st.success("Settings updated successfully!")
            st.cache_data.clear()


def read_sql(conn: GSheetsConnection, ddl: str) -> pd.DataFrame:
    """Executes a SQL query using a GSheetsConnection"""

    if ddl.endswith(".sql"):
        with open(ddl, "r") as f:
            sql = f.read()

        return conn.query(sql)
    else:
        return conn.query(sql)


def get_active_accounts(conn: GSheetsConnection) -> pd.DataFrame:
    """Fetches active accounts from the Google Sheet."""
    df = conn.read(worksheet="accounts")
    df = df[
        (
            pd.to_datetime(df["effective_start_date"], errors="coerce")
            <= pd.to_datetime(date.today())
        )
        & (
            pd.to_datetime(df["effective_end_date"], errors="coerce").fillna(
                pd.to_datetime("2262-04-11")
            )
            > pd.to_datetime(date.today())
        )
    ]
    return df


def get_balance_records(conn: GSheetsConnection) -> pd.DataFrame:
    df = conn.read(worksheet="balances")
    return df


@st.dialog("Add Balance Records", width="large")
def add_balance_records(conn: GSheetsConnection):
    # Get today's date
    today = datetime.today().strftime("%m/%d/%Y")

    # Get list of active accounts
    df = get_active_accounts(conn=conn)

    # Add default columns for today's balance entry
    df["full_date"] = today
    df["balance"] = None  # balance to be filled in manually

    # Load existing balance records
    current_balance_records = load_worksheet(conn=conn, worksheet="balances")

    # Clear previous form submission from session state
    st.session_state["records_to_upload"] = None

    with st.form("add_balance_form"):
        # Render editable table for user to input balances
        new_records_df = st.data_editor(
            data=df,
            use_container_width=True,
            column_order=["institution_name", "account_name", "full_date", "balance"],
            num_rows="fixed",
            disabled=("institution_name", "account_name"),
            hide_index=True,
        )

        # Handle form submission
        submitted = st.form_submit_button("Save")

        if submitted:

            # Check for missing balances
            if new_records_df["balance"].isnull().any():
                st.error("Please enter a balance for all accounts before saving.")

            # Check for non-numeric values
            elif (
                not pd.to_numeric(new_records_df["balance"], errors="coerce")
                .notnull()
                .all()
            ):
                st.error("All balances must be numeric (integer or float).")

            # Check for valid date format and consistency
            elif (
                new_records_df["full_date"].nunique() != 1
                or not new_records_df["full_date"]
                .apply(
                    lambda d: isinstance(d, str)
                    and pd.to_datetime(d, format="%m/%d/%Y", errors="coerce")
                )
                .notnull()
                .all()
            ):
                st.error(
                    "Please ensure all dates are the same and in MM/DD/YYYY format."
                )

            # Check if the date is already in the balance records
            elif (
                pd.to_datetime(new_records_df["full_date"]).iloc[0].strftime("%m/%d/%Y")
            ) in (
                pd.to_datetime(current_balance_records["full_date"], errors="coerce")
                .dt.strftime("%m/%d/%Y")
                .dropna()
                .tolist()
            ):
                st.error(
                    f"Records for {new_records_df['full_date'].unique()}'s date already exist. Please update existing records instead."
                )

            # If all validations pass, store the new records in session state
            else:
                # Clean and store validated data
                new_records_df["balance"] = new_records_df["balance"].astype(float)
                # Drop metadata columns that shouldn't be uploaded
                cleaned_df = new_records_df.drop(
                    columns=["effective_start_date", "effective_end_date"],
                    errors="ignore",
                )
                st.session_state["records_to_upload"] = cleaned_df

    # Proceed if data was successfully validated and submitted
    if st.session_state["records_to_upload"] is not None:
        new_records = st.session_state["records_to_upload"]

        # Append and upload the new records
        updated_records = pd.concat(
            [current_balance_records, new_records], ignore_index=True
        )
        updated_records.drop(columns=["balance_type"], inplace=True)

        conn.update(worksheet="balances", data=updated_records)

        st.success("Records saved successfully!")


def edit_balance_records(conn: GSheetsConnection):
    # Create a button to open the URL
    st.link_button(
        label="Edit",
        url=st.secrets["connections"]["gsheets"]["spreadsheet"],
        type="secondary",
        use_container_width=True,
    )


def delete_balance_records(conn: GSheetsConnection):
    # Create a button to open the URL
    st.link_button(
        label="Delete",
        url=st.secrets["connections"]["gsheets"]["spreadsheet"],
        type="secondary",
        use_container_width=True,
    )


def edit_transaction_records(conn: GSheetsConnection):
    # Create a button to open the URL
    st.link_button(
        label="Edit",
        url=st.secrets["connections"]["gsheets"]["spreadsheet"],
        type="secondary",
        use_container_width=True,
    )


def delete_transaction_records(conn: GSheetsConnection):
    # Create a button to open the URL
    st.link_button(
        label="Delete",
        url=st.secrets["connections"]["gsheets"]["spreadsheet"],
        type="secondary",
        use_container_width=True,
    )
