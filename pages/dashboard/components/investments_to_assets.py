import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
from streamlit_extras.stylable_container import stylable_container

from utilities.gsheets import load_worksheet
from pages.dashboard.functions.charts import percent_to_target__chart

from utilities.calculations import *

TARGET_INVESTMENT_TO_ASSET_RATE = 0.85


@st.dialog("Investments to Assets")
def investments_to_assets__dialog(df):
    """
    Display a dialog with two tabs: one for a investment-to-assets vs. target chart,
    and another for a data table. Also provides a download button for the data.
    """

    st.caption(
        f"The target Investment-to-Asset Ratio is {TARGET_INVESTMENT_TO_ASSET_RATE*100:,.0f}%."
    )

    # Create tabs
    chart_tab, table_tab = st.tabs(["Chart", "Table"])

    # --- Table Tab ---
    with table_tab:
        st.dataframe(
            df,
            column_order=[
                "full_date",
                "total_investments",
                "investment_to_asset_rate",
                "percent_to_target",
            ],
            hide_index=True,
            column_config={
                "full_date": st.column_config.DateColumn("Date"),
                "total_investments": st.column_config.NumberColumn(
                    "Investments", format="dollar"
                ),
                "networth": st.column_config.NumberColumn("Net Worth", format="dollar"),
                "investment_to_asset_rate": st.column_config.NumberColumn(
                    "Investments-to-Asset Rate", format="percent"
                ),
                "percent_to_target": st.column_config.NumberColumn(
                    "Percent", format="percent"
                ),
            },
        )

    with chart_tab:
        st.markdown("#### Progress to Investments-to-Assets Target")
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


def investments_to_assets_tile(conn: GSheetsConnection):
    """ """

    df = conn.query(
        """
        select
          full_date
        , sum(balance) as networth
        , sum(case when category = 'Investments' then balance end) as total_investments
        , total_investments / networth as investment_to_asset_rate
        from balances
        group by full_date
    """
    )
    df["full_date"] = pd.to_datetime(df["full_date"])
    df["percent_to_target"] = (
        df["investment_to_asset_rate"] / TARGET_INVESTMENT_TO_ASSET_RATE
    )
    df = df.sort_values(by=["full_date"]).reset_index(drop=True)

    current_rate = df.loc[df["full_date"].idxmax(), "investment_to_asset_rate"]
    progress = df.loc[df["full_date"].idxmax(), "percent_to_target"]

    ## CREATE TILE
    with stylable_container(
        key="investments_to_assets",
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
            st.markdown("##### Investments-to-Assets")
        with titlecols[1]:
            if st.button(
                "☰ View", use_container_width=True, key="investments_to_assets"
            ):
                investments_to_assets__dialog(df=df)
        st.metric(
            "Investment-to-Assets",
            value=f"{current_rate*100:,.1f}%",
            label_visibility="collapsed",
        )
        st.progress(
            value=np.minimum(progress, 1),
            text=f"Percent to Target: **{progress*100:.1f}%**",
        )
