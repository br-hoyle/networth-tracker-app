import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import date, datetime


def refresh_connection() -> GSheetsConnection:
    if st.button("Refresh Data", type="secondary", use_container_width=True):
        st.cache_data.clear()


def read_sql(conn: GSheetsConnection, ddl: str) -> pd.DataFrame:
    """Executes a SQL query using a GSheetsConnection"""

    if ddl.endswith(".sql"):
        with open(ddl, "r") as f:
            sql = f.read()

        return conn.query(sql)
    else:
        return conn.query(sql)


def load_worksheet(conn: GSheetsConnection, worksheet: str) -> pd.DataFrame:
    return conn.read(worksheet=worksheet)


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
            >= pd.to_datetime(date.today())
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
