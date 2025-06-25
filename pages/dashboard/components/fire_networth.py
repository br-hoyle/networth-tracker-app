import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
from streamlit_extras.stylable_container import stylable_container

from utilities.gsheets import load_worksheet
from pages.dashboard.functions.charts import percent_to_target__chart

from utilities.calculations import *
from utilities.helper import *
from pages.dashboard.functions.charts import *


@st.dialog("Financial Independence")
def financial_independence_track__dialog(df: pd.DataFrame):
    """
    Display a dialog with two tabs: one for a net worth target for financial independence vs. target chart,
    and another for a data table. Also provides a download button for the data.
    """
    # Create tabs
    chart_tab, table_tab = st.tabs(["Chart", "Table"])

    # --- Table Tab ---
    with table_tab:
        st.dataframe(
            df,
            hide_index=True,
            column_config={
                "full_date": st.column_config.DateColumn("Date"),
                "total_income": st.column_config.NumberColumn(
                    "Income", format="dollar"
                ),
                "networth": st.column_config.NumberColumn("Net Worth", format="dollar"),
                "financial_independence_target": st.column_config.NumberColumn(
                    "FIRE Target", format="dollar"
                ),
                "percent_to_target": st.column_config.NumberColumn(
                    "Percent", format="percent"
                ),
            },
        )

    with chart_tab:
        st.markdown("#### Progress to Financial Independence")
        st.plotly_chart(
            percent_to_target__chart(df=df),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    # --- Download Button ---
    st.download_button(
        label="Download",
        data=df.to_csv(index=False),
        icon=":material/download:",
        file_name="progress_to_fire_target.csv",
    )


def financial_independence_tile(conn: GSheetsConnection):

    # --- Load and prepare net worth data ---
    networth_df = (
        load_worksheet(conn=conn, worksheet="balances")
        .groupby("full_date")["balance"]
        .sum()
        .reset_index()
        .rename(columns={"balance": "networth"})
        .assign(full_date=lambda df: pd.to_datetime(df["full_date"]))
        .sort_values("full_date")
    )

    # --- Load balances and income data ---
    balances_df = conn.query("SELECT DISTINCT full_date FROM balances;")
    income_df = conn.read(worksheet="income")

    # Ensure datetime format for date comparisons
    balances_df["full_date"] = pd.to_datetime(balances_df["full_date"])
    income_df["effective_start_date"] = pd.to_datetime(
        income_df["effective_start_date"]
    )
    income_df["effective_end_date"] = pd.to_datetime(
        income_df["effective_end_date"], errors="coerce"
    ).fillna(datetime.today())

    # --- Build time series of total income by full_date ---
    result_df = balances_df.copy()
    result_df["total_income"] = result_df["full_date"].apply(
        lambda date: income_df[
            (income_df["effective_start_date"] <= date)
            & (income_df["effective_end_date"] >= date)
        ]["income"].sum()
    )

    # Calculate dynamic FI target and merge with net worth
    result_df["financial_independence_target"] = (
        result_df["total_income"] * st.session_state["replacement_income_rate"]
    ) / 0.04
    result_df = result_df.merge(
        networth_df[["full_date", "networth"]], on="full_date", how="inner"
    )
    result_df["percent_to_target"] = (
        result_df["networth"] / result_df["financial_independence_target"]
    )
    result_df = result_df.sort_values(by=["full_date"], ascending=True)

    fire_number = result_df.loc[result_df["full_date"].idxmax()][
        "financial_independence_target"
    ]
    progress = result_df.loc[result_df["full_date"].idxmax()]["networth"] / fire_number

    with stylable_container(
        key="financial_independence_target",
        css_styles=f"""
            {{
                background-color: #e3d8cc;
                padding: 1rem 1rem 2rem 1rem;
                border-radius: 0.5rem;
                border-width: 0px;
                border-style: solid;
            }}
        """,
    ):

        titlecols = st.columns([7, 3])
        with titlecols[0]:
            st.markdown("##### Financial Independence")
        with titlecols[1]:
            if st.button("☰ View", use_container_width=True, key="fi_track"):
                financial_independence_track__dialog(df=result_df)
        st.metric(
            "Financial Independence Track",
            value=f"${fire_number:,.0f}",
            label_visibility="collapsed",
        )
        st.progress(
            value=np.minimum(progress, 1),
            text=f"Progress to Target: **{progress:,.1%}**",
        )
