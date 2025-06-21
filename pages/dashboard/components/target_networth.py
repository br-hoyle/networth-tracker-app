import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
from streamlit_extras.stylable_container import stylable_container

from utilities.gsheets import load_worksheet
from pages.dashboard.functions.charts import percent_to_target__chart

from utilities.calculations import *


@st.dialog("Target Networth")
def target_networth_rate__dialog(df: pd.DataFrame):
    """
    Display a dialog with two tabs: one for a net worth vs. target chart,
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
                "age": st.column_config.NumberColumn("Age"),
                "networth": st.column_config.NumberColumn("Net Worth", format="dollar"),
                "target_networth": st.column_config.NumberColumn(
                    "Target Net Worth", format="dollar"
                ),
                "percent_to_target": st.column_config.NumberColumn(
                    "Percent", format="percent"
                ),
            },
        )

    # --- Chart Tab ---
    with chart_tab:
        st.markdown("#### Progress to Target Networth")

        # Render chart
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
        file_name="target_networth_df.csv",
    )


def target_networth_tile(conn: GSheetsConnection):

    # --- Load and prepare net worth data ---
    networth_df = (
        load_worksheet(conn=conn, worksheet="balances")
        .groupby("full_date")["balance"]
        .sum()
        .reset_index()
        .rename(columns={"balance": "networth"})
    )
    networth_df["full_date"] = pd.to_datetime(networth_df["full_date"])
    networth_df = networth_df.sort_values("full_date")

    # --- Calculate overall target and progress ---
    current_age = calculate_age(from_date=st.session_state["birthdate"])
    income = conn.query(
        "select sum(income) as total_income from income where effective_end_date = '12/31/9999';"
    )
    total_income = income["total_income"].loc[0]
    target_networth = calculate_target_networth(
        income=total_income,
        target_savings_rate=st.session_state["target_savings_rate"],
        target_return_on_investment=st.session_state["target_return_on_investment"],
        age=current_age,
    )
    current_networth = networth_df["networth"].iloc[-1]
    percent_to_target = current_networth / target_networth

    # Calculate age and target net worth directly using apply
    target_networth_df = networth_df[["full_date"]].copy()
    target_networth_df["age"] = target_networth_df["full_date"].apply(
        lambda date: calculate_age(
            from_date=st.session_state["birthdate"], to_date=date
        )
    )

    target_networth_df["target_networth"] = target_networth_df["age"].apply(
        lambda age: calculate_target_networth(
            income=total_income,
            target_savings_rate=st.session_state["target_savings_rate"],
            target_return_on_investment=st.session_state["target_return_on_investment"],
            age=age,
        )
    )

    # Add networth and percent-to-target columns
    target_networth_df["networth"] = networth_df["networth"]
    target_networth_df["percent_to_target"] = (
        target_networth_df["networth"] / target_networth_df["target_networth"]
    )

    ## CREATE TILE
    with stylable_container(
        key="target_networth",
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

        ## DISPLAY
        titlecols = st.columns([7, 3])
        with titlecols[0]:
            st.markdown("##### Target Networth")
        with titlecols[1]:
            if st.button("☰ View", use_container_width=True, key="target_networth"):
                target_networth_rate__dialog(df=target_networth_df)
        st.metric(
            "Financial Independence Ratio",
            value=f"${target_networth:,.0f}",
            label_visibility="collapsed",
        )
        st.progress(
            value=np.minimum(percent_to_target, 1),
            text=f"Percent to Target: **{percent_to_target*100:.1f}%**",
        )
