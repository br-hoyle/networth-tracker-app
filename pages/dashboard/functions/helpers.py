import streamlit as st
from utilities.auth import *
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go
from streamlit_extras.stylable_container import stylable_container

from utilities.sidebar import show_app_sidebar
from utilities.helper import *
from utilities.gsheets import *


def balances_spreadsheet(conn: GSheetsConnection):

    # Read Balances (convert to datetime, and round balance)
    balances_df = conn.read(worksheet="balances").assign(
        full_date=lambda x: pd.to_datetime(x["full_date"]),
        balance=lambda x: x["balance"].round(2),
    )

    # Read Recent Categorized Balances
    recent_category_balances_df = read_sql(
        conn=conn, ddl="pages/dashboard/ddl/categorized_balances_most_recent.sql"
    )

    # Create a column per category balance
    cols = st.columns(len(recent_category_balances_df))

    # Display balance vs previous balance
    for i, row in recent_category_balances_df.iterrows():
        with cols[i]:
            with stylable_container(
                key=row["cat"],
                css_styles="""
                    {
                        background-color: #ecebe3;
                        padding: 1rem 1rem 2rem 1rem;  /* top right bottom left */
                        border-radius: 0.5rem;
                        border-width: 1px;
                        border-style: solid;
                        border-color: #3d3a2a;
                    }
                """,
            ):
                st.metric(
                    label=row["cat"],  # or another label like f"{row['cat']} Balance"
                    value=f"${row['current_balance']:,.0f}",
                    delta=f"{'-$' if (row['current_balance'] - row['last_balance']) < 0 else '$'}{abs((row['current_balance'] - row['last_balance'])):,.2f} vs. previous balance",
                    delta_color="normal",  # or use "inverse"/"off"/"normal" as needed
                )

    # Pivot Long Balances to Wide-on-Account Balances
    balances_df_pivot = balances_df.pivot(
        index="full_date",
        values="balance",
        columns=[
            "institution_name",
            "account_name",
        ],
    ).fillna(0)

    # Add the 'Total' column by summing across all existing columns
    total_col = (
        "Total",
        "Networth",
    )
    balances_df_pivot[total_col] = balances_df_pivot.sum(axis=1)

    # Reorder columns
    balances_df_pivot = balances_df_pivot[
        [total_col] + [col for col in balances_df_pivot.columns if col != total_col]
    ]

    # Show DataFrame (ordered full_date desc)
    st.dataframe(
        balances_df_pivot.sort_values(by="full_date", ascending=False),
        column_config={
            "full_date": st.column_config.DateColumn("Date", format="MM/DD/YYYY"),
        },
        height=550,
    )

    # Download Button
    st.download_button(
        label="Download CSV",
        data=convert_for_download(balances_df_pivot),
        file_name="data.csv",
        mime="text/csv",
        icon=":material/download:",
    )
