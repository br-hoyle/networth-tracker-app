import streamlit as st
import pandas as pd
import numpy as np

from streamlit_gsheets import GSheetsConnection
from streamlit_extras.stylable_container import stylable_container

from utilities.auth import *
from utilities.helper import *
from utilities.gsheets import *


def style_and_render_metric(group: str, amount: float, key_suffix: str):
    """
    Renders a single metric inside a stylable container with appropriate color logic.
    """
    is_income_or_savings = group in ["Income", "Savings"]
    secondary_bg = (
        get_config_value("theme.ColorPalette.green")
        if is_income_or_savings
        else get_config_value("theme.ColorPalette.secondaryBackgroundColor")
    )
    text_color = get_config_value("theme.ColorPalette.textColor")

    display_value = (
        f"{'-' if amount < 0 or group == 'Savings' else ''}${abs(int(amount)):,}"
    )

    with stylable_container(
        key=f"spreadsheet_headers_{key_suffix}",
        css_styles=f"""
            {{
                background-color: {secondary_bg};
                font-weight: bold;
                padding: 1rem 1rem 2rem 1rem;
                border-radius: 0.5rem;
                border-color: {text_color};
                border-width: 0px;
                border-style: solid;
            }}
        """,
    ):
        st.metric(label=group, value=display_value)


def transactions_spreadsheet(conn: GSheetsConnection):
    # Read categorized transaction data grouped by month
    transactions_group_by_month_df = read_sql(
        conn=conn, ddl="pages/income_and_expenses/ddl/transaction_groups_by_month.sql"
    )

    # Pivot and compute savings as total of all columns
    pivoted_df = (
        transactions_group_by_month_df.pivot(
            index="full_date", columns="group", values="total_amount"
        )
        .fillna(0)
        .reset_index()
    )
    pivoted_df["Savings"] = pivoted_df.drop(columns=["full_date"]).sum(axis=1)

    # UI Container for header and slider
    with stylable_container(
        key="spreadsheet_headers",
        css_styles="""
            {
                background-color: #e3d8cc;
                padding: 1rem 1rem 2rem 1rem;
                border-radius: 0.5rem;
                border-width: 0px;
                border-style: solid;
            }
        """,
    ):
        header_col, slider_col = st.columns([8, 2])
        with slider_col:
            selected_slider = st.slider(
                label="**Average Period (Months):**",
                min_value=3,
                max_value=len(pivoted_df),
                value=6,
            )
        with header_col:
            st.markdown(f"#### Average Spent Over {selected_slider} Months")

        # Compute average amounts for the selected number of months
        average_df = (
            pivoted_df.tail(selected_slider)
            .drop(columns=["full_date"])
            .mean()
            .reset_index()
            .rename(columns={"index": "group", 0: "amount"})
        )

        # Filter and sort average amounts
        average_df = (
            average_df[average_df["amount"] != 0]
            .assign(
                _positive=lambda df: df["amount"] > 0,
                _sort_key=lambda df: df["amount"].apply(
                    lambda x: abs(x) if x < 0 else x
                ),
            )
            .sort_values(by=["_positive", "_sort_key"], ascending=[False, False])
            .drop(columns=["_positive", "_sort_key"])
            .reset_index(drop=True)
        )

        groups_to_show = len(average_df)

        # Show top 8 average groups as metrics
        top_cols = st.columns(min(groups_to_show, 8))
        for col, (_, row) in zip(top_cols, average_df.iterrows()):
            with col:
                style_and_render_metric(
                    row["group"], row["amount"], key_suffix=row["group"]
                )

        # Show remaining groups in an expander if more than 8
        if groups_to_show > 8:
            with st.expander("Click to Show More Expense Groups"):
                extra_cols = st.columns(max(4, groups_to_show - 8))
                for col, (_, row) in zip(extra_cols, average_df.iloc[8:].iterrows()):
                    with col:
                        style_and_render_metric(
                            row["group"], row["amount"], key_suffix=row["group"]
                        )

    # Reorder columns in the pivoted DataFrame
    displayed_columns = (
        ["full_date"]
        + list(average_df["group"])
        + [
            col
            for col in pivoted_df.columns
            if col not in list(average_df["group"]) and col != "full_date"
        ]
    )

    # Show full pivoted table
    st.dataframe(
        pivoted_df[displayed_columns].sort_values(by="full_date", ascending=False),
        hide_index=True,
        column_config={
            "full_date": st.column_config.DateColumn(
                "Month", format="MMM YYYY", width="small", pinned=True
            ),
            **{
                col: st.column_config.NumberColumn(format="dollar", width="small")
                for col in displayed_columns
                if col != "full_date"
            },
        },
        height=500,
        use_container_width=True,
    )

    # Download Button
    st.download_button(
        label="Download CSV",
        data=convert_for_download(pivoted_df),
        file_name="monthly_transaction_amount.csv",
        mime="text/csv",
        icon=":material/download:",
    )
