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


## ---------- BALANCES SPREADSHEET ---------- ##
elif view_type == "Spreadsheet":

    balances_spreadsheet(conn=conn)


# # Ensure correct formatting and sort
# df["full_date"] = pd.to_datetime(df["full_date"])
# df = df.sort_values("full_date")

# # Select last 11 unique dates
# last_n_dates = df["full_date"].drop_duplicates().sort_values().iloc[-6:]
# df_filtered = df[df["full_date"].isin(last_n_dates)]

# # Pivot: institution balances by date
# pivot_df = df_filtered.pivot_table(
#     index=["category", "institution_name"],
#     columns="full_date",
#     values="balance",
#     aggfunc="sum",
# ).sort_index(axis=1)

# # ✅ Rename columns: safely convert datetime columns to strings
# pivot_df.columns = [
#     col.strftime("%Y-%m-%d") if isinstance(col, pd.Timestamp) else col
#     for col in pivot_df.columns
# ]

# # ✅ Identify balance columns (all except the last two for change columns)
# balance_columns = (
#     pivot_df.columns[:-2] if "Last Change" in pivot_df.columns else pivot_df.columns
# )

# # Compute changes
# last_vals = pivot_df[balance_columns[-1]]
# prev_vals = pivot_df[balance_columns[-2]]
# change_1 = ((last_vals - prev_vals) / prev_vals.replace(0, np.nan)) * 100
# change_10 = (
#     (last_vals - pivot_df[balance_columns[0]])
#     / pivot_df[balance_columns[0]].replace(0, np.nan)
# ) * 100

# # Add changes
# pivot_df["Last Change"] = change_1
# pivot_df["Change"] = change_10

# # Recalculate balance_columns since two new columns were just added
# balance_columns = [
#     col for col in pivot_df.columns if col not in ["Last Change", "Change"]
# ]

# # Add Balance History list column
# pivot_df["Balance History"] = pivot_df[balance_columns].values.tolist()

# # Reset index for display
# final_df = pivot_df.reset_index()

# # ✅ Add Total rows by category
# tables = {}
# for category in final_df["category"].unique():
#     df_cat = final_df[final_df["category"] == category].copy()

#     # Calculate numeric totals
#     numeric_data = (
#         df_cat[balance_columns].replace("[\$,]", "", regex=True).astype(float)
#     )
#     total_numeric = numeric_data.sum()
#     last = total_numeric.iloc[-1]
#     prev = total_numeric.iloc[-2]
#     first = total_numeric.iloc[0]
#     delta_last = ((last - prev) / prev) * 100 if prev != 0 else 0
#     delta_10 = ((last - first) / first) * 100 if first != 0 else 0

#     # Build total row
#     total_row = {
#         "category": "",  # remove category label from total
#         "institution_name": "Total",
#         "Last Change": delta_last,
#         "Change": delta_10,
#         "Balance History": total_numeric.tolist(),
#     }

#     for i, date_col in enumerate(balance_columns):
#         total_row[date_col] = total_numeric.iloc[i]

#     df_cat = pd.concat([df_cat, pd.DataFrame([total_row])], ignore_index=True)
#     tables[category] = df_cat

# # ✅ Display using Streamlit
# for category, table in tables.items():
#     st.subheader(category)

#     num_date_cols = [col for col in table.columns if col[:4].isdigit()]

#     # Define row-level color logic for the line chart
#     line_colors = [
#         "green" if row["Balance History"][0] < row["Balance History"][-1] else "red"
#         for _, row in table.iterrows()
#     ]

#     def highlight_status(val):
#         color = "#487631" if val >= 0 else "#933838"
#         return f"color: {color}"

#     # Assuming you have a DataFrame named 'df' with a 'Status' column
#     df_styled = table.fillna(0).style.applymap(
#         highlight_status, subset=["Last Change", "Change"]
#     )

#     st.dataframe(
#         df_styled,
#         column_order=["institution_name"]
#         + balance_columns
#         + [
#             "Balance History",
#             "Last Change",
#             "Change",
#         ],
#         column_config={
#             "institution_name": st.column_config.TextColumn(
#                 "Institution", width="medium"
#             ),
#             "Balance History": st.column_config.LineChartColumn(
#                 "Balance Trend",
#                 y_min=0,
#                 # line_color=line_colors,
#             ),
#             "Last Change": st.column_config.NumberColumn(
#                 format="%.2f%%",
#                 help="Change from previous date",
#                 width="small",
#             ),
#             "Change": st.column_config.NumberColumn(
#                 format="%.2f%%",
#                 help="Change from 10 periods ago",
#                 width="small",
#             ),
#             **{
#                 col: st.column_config.NumberColumn(
#                     format="dollar",
#                     help=f"Balance on {col}",
#                     width="small",
#                 )
#                 for col in num_date_cols
#             },
#         },
#         hide_index=True,
#         use_container_width=True,
#     )
