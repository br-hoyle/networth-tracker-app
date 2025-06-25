import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from streamlit_extras.stylable_container import stylable_container

from utilities.gsheets import load_worksheet
from pages.dashboard.functions.charts import networth__chart


@st.dialog("Net Worth")
def networth_over_time__dialog(df: pd.DataFrame):
    st.dataframe(
        df,
        hide_index=True,
        column_config={
            "full_date": st.column_config.DateColumn("Date"),
            "networth": st.column_config.NumberColumn("Networth", format="dollar"),
        },
    )
    st.download_button(
        label="Download",
        data=df.to_csv(),
        icon=":material/download:",
        file_name="networth_over_time.csv",
    )


def networth_tile(conn: GSheetsConnection):

    ## LOAD DATA
    balance_df = load_worksheet(conn=conn, worksheet="balances")
    df = (balance_df.groupby("full_date")["balance"].sum().reset_index()).rename(
        columns={"balance": "networth"}
    )

    # Ensure full_date is a datetime object and sort
    df["full_date"] = pd.to_datetime(df["full_date"])
    df = df.sort_values("full_date")

    ## CREATE TILE
    with stylable_container(
        key="networth_component",
        css_styles=f"""
            {{
                background-color: #e3d8cc;
                padding: 1rem 1rem 1rem 1rem;
                border-radius: 0.5rem;
                border-width: 0px;
                border-style: solid;
            }}
        """,
    ):
        # Right-aligned metric
        col1, col2 = st.columns([8, 2])
        with col1:
            st.markdown("### Net Worth")
            st.metric(
                label="Net Worth",
                label_visibility="collapsed",
                value=f"${df['networth'].iloc[-1]:,.0f}",
                delta=(
                    f"{'-$' if df['networth'].iloc[-1] - df['networth'].iloc[-2] < 0 else '$'}"
                    f"{abs(df['networth'].iloc[-1] - df['networth'].iloc[-2]):,.2f} vs. previous balance"
                ),
            )
        with col2:
            if st.button("☰ View", use_container_width=True):
                networth_over_time__dialog(df=df)

        st.plotly_chart(
            networth__chart(df=df),
            use_container_width=True,
            config={"displayModeBar": False},
        )
