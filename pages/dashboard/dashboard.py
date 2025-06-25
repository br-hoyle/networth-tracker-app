import streamlit as st
from utilities.auth import *
from streamlit_gsheets import GSheetsConnection

from utilities.sidebar import show_app_sidebar
from utilities.helper import *
from utilities.gsheets import *
from utilities.calculations import *

from pages.dashboard.functions.helpers import *

from pages.dashboard.components.networth import networth_tile
from pages.dashboard.components.target_networth import target_networth_tile
from pages.dashboard.components.fire_networth import financial_independence_tile
from pages.dashboard.components.investments_to_assets import investments_to_assets_tile
from pages.dashboard.components.retirement_margin import retirement_margin_tile
from pages.dashboard.components.balance_by_group import balance_by_group_tile

import numpy as np

# ----------------- HEADER ----------------- #
st.set_page_config(layout="wide", page_title="Product Dashboard")

view_type = show_app_sidebar()

# Initialize Connection & Check for Staleness
conn = st.connection("gsheets", type=GSheetsConnection)
load_settings_to_session_state(conn=conn)

header_cols = st.columns([7, 1, 1])
with header_cols[0]:
    st.title("Networth Dashboard")
with header_cols[1]:
    st.write("")
    st.write("")
    refresh_connection()
with header_cols[2]:
    st.write("")
    st.write("")
    if st.button("☰ Settings", type="secondary", use_container_width=True):
        settings_assumptions(conn=conn)

check_balance_staleness(conn)

## ----------- BALANCES DASHBOARD ----------- ##
if view_type == "Dashboard":

    row_one_columns = st.columns([4, 3, 3])

    # NETWORTH OVER TIME
    with row_one_columns[0]:
        networth_tile(conn=conn)

    # SUPPORTING NETWORTH MEASURES
    with row_one_columns[1]:

        ## TARGET NETWORTH
        target_networth_tile(conn=conn)

        ## INVESTMENTS TO ASSETS
        investments_to_assets_tile(conn=conn)

    with row_one_columns[2]:

        ## FINANCIAL INDEPENDENCE TRACK
        financial_independence_tile(conn=conn)

        ## RETIREMENT MARGIN
        retirement_margin_tile(conn=conn)

    # BALANCE BY GROUP
    balance_by_group_tile(conn=conn)


## ---------- BALANCES SPREADSHEET ---------- ##
elif view_type == "Spreadsheet":

    balances_spreadsheet(conn=conn)


with stylable_container(
    key="table_tile",
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
    columns_ = st.columns([8, 2])
    with columns_[0]:
        st.markdown("### Recent Balance Changes")
        st.write(
            "Display recent balance trends by institution and category. Use the slider to adjust how many recent entries are included. \n"
        )
    with columns_[1]:
        with stylable_container(
            key="slider_tile",
            css_styles="""
                    {
                background-color: #ecebe3;
                padding: 1rem 1rem 2rem 1rem;
                border-radius: 0.5rem;
                border-width: 0px;
                border-style: solid;
                }
                """,
        ):
            user_selected = st.slider(
                label="Number of Previous Entries to Show",
                min_value=3,
                max_value=10,
                value=6,
            )
    st.markdown("<hr style='border: 1px solid black;' />", unsafe_allow_html=True)

    # Load and preprocess
    df = conn.read(worksheet="balances")
    df["full_date"] = pd.to_datetime(df["full_date"])
    df = df.sort_values("full_date")

    # Filter to last 6 unique dates
    last_n_dates = df["full_date"].drop_duplicates().sort_values().iloc[-user_selected:]
    df_filtered = df[df["full_date"].isin(last_n_dates)]

    # Pivot by category and institution
    pivot_df = df_filtered.pivot_table(
        index=["category", "institution_name"],
        columns="full_date",
        values="balance",
        aggfunc="sum",
    ).sort_index(axis=1)

    # Format column names
    pivot_df.columns = [
        col.strftime("%Y-%m-%d") if isinstance(col, pd.Timestamp) else col
        for col in pivot_df.columns
    ]

    # Determine balance columns
    balance_columns = (
        pivot_df.columns[:-2] if "Last Change" in pivot_df.columns else pivot_df.columns
    )

    # Compute percentage changes
    last_vals = pivot_df[balance_columns[-1]]
    prev_vals = pivot_df[balance_columns[-2]]
    first_vals = pivot_df[balance_columns[0]]

    change_1 = ((last_vals - prev_vals) / prev_vals.replace(0, np.nan)) * 100
    change_10 = ((last_vals - first_vals) / first_vals.replace(0, np.nan)) * 100

    pivot_df["Last Change"] = change_1
    pivot_df["Change"] = change_10

    # Recompute balance columns (now that we added change columns)
    balance_columns = [
        col for col in pivot_df.columns if col not in ["Last Change", "Change"]
    ]

    # Add balance history
    pivot_df["Balance History"] = pivot_df[balance_columns].values.tolist()

    # Reset index for display
    final_df = pivot_df.reset_index().fillna(0)

    # Build summary tables by category
    tables = {}

    for category in final_df["category"].unique():
        df_cat = final_df[final_df["category"] == category].copy()

        # Total row
        numeric_data = df_cat[balance_columns].astype(float)
        total_numeric = numeric_data.sum()

        last = total_numeric.iloc[-1]
        prev = total_numeric.iloc[-2]
        first = total_numeric.iloc[0]

        delta_last = ((last - prev) / prev) * 100 if prev != 0 else 1
        delta_10 = ((last - first) / first) * 100 if first != 0 else 1

        total_row = {
            "category": "",
            "institution_name": "Total",
            "Last Change": delta_last,
            "Change": delta_10,
            "Balance History": total_numeric.tolist(),
        }

        for i, col in enumerate(balance_columns):
            total_row[col] = total_numeric.iloc[i]

        df_cat = pd.concat([df_cat, pd.DataFrame([total_row])], ignore_index=True)
        tables[category] = df_cat

    # Step 3: Before styling, add improvement flags to your table

    for category, table in tables.items():

        num_date_cols = [col for col in table.columns if col[:4].isdigit()]
        first_date_col = num_date_cols[0]
        prev_date_col = num_date_cols[-2]
        last_date_col = num_date_cols[-1]

        def highlight_change(row, col):
            first = row[first_date_col]
            prev = row[prev_date_col]
            last = row[last_date_col]
            val = row[col]

            if pd.isna(val):
                return ""

            if col == "Last Change":
                improved = last >= prev
            else:
                improved = last >= first

            if improved:
                return f"""background-color: {get_config_value('theme.ColorPalette.green')}; color: #2c6a3a"""  # light green
            else:
                return f"background-color: {get_config_value('theme.ColorPalette.red')}; color: #76333c"  # light red

        def style_table(df):
            style_df = pd.DataFrame("", index=df.index, columns=df.columns)

            for i in df.index:
                is_total_row = df.loc[i, "institution_name"] == "Total"

                for col in df.columns:
                    style = ""

                    if is_total_row:
                        style += f"; background-color: {get_config_value('theme.ColorPalette.secondaryBackgroundColor')}; font-weight: bold;"

                    if col in ["Last Change", "Change"]:
                        style = highlight_change(df.loc[i], col)

                    style_df.at[i, col] = style.strip("; ")

            return style_df

        df_styled = table.style.apply(style_table, axis=None)

        st.markdown(f"##### {category}")

        st.dataframe(
            df_styled,
            column_order=["institution_name"]
            + balance_columns
            + ["Balance History", "Last Change", "Change"],
            column_config={
                "institution_name": st.column_config.TextColumn(
                    "Institution", width="medium"
                ),
                "Balance History": st.column_config.AreaChartColumn(
                    "Balance Trend", y_min=0
                ),
                "Last Change": st.column_config.NumberColumn(
                    format="%.2f%%", help="Change from previous date", width="small"
                ),
                "Change": st.column_config.NumberColumn(
                    format="%.2f%%", help="Change from first date", width="small"
                ),
                **{
                    col: st.column_config.NumberColumn(
                        format="dollar",
                        help=f"Balance on {col}",
                        width="small",
                    )
                    for col in balance_columns
                },
            },
            hide_index=True,
            use_container_width=True,
        )
