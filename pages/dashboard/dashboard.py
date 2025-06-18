import streamlit as st
from utilities.auth import *
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go
from streamlit_extras.stylable_container import stylable_container

from utilities.sidebar import show_app_sidebar
from utilities.helper import *
from utilities.gsheets import *

from pages.dashboard.functions import balances_spreadsheet, settings_assumptions

st.set_page_config(layout="wide", page_title="Product Dashboard")

view_type = show_app_sidebar()

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
        settings_assumptions()

# Initialize Connection & Check for Staleness
conn = st.connection("gsheets", type=GSheetsConnection)
check_balance_staleness(conn)

if view_type == "Dashboard":
    st.write("Dashboard")

elif view_type == "Spreadsheet":

    balances_spreadsheet(conn=conn)


# with st.sidebar:

#     # Control
#     st.segmented_control(
#         "**View**",
#         options=["Dashboard", "Spreadsheet"],
#         key="nav",
#         selection_mode="single",
#         default=["Dashboard"],
#     )

#     # Balances
#     st.markdown("##### **Balances**")

#     def add_balance_dialog():
#         if st.button("**Add**", type="primary", use_container_width=True):
#             st.write("Please log in to add balances.")

#     add_balance_dialog()

#     balance_cols = st.columns(2)
#     with balance_cols[0]:

#         def edit_balance_dialog():
#             if st.button("Edit", type="secondary", use_container_width=True):
#                 st.write("Please log in to add balances.")

#         edit_balance_dialog()

#     with balance_cols[1]:

#         def remove_balance_dialog():
#             if st.button("Remove", type="secondary", use_container_width=True):
#                 st.write("Please log in to add balances.")

#         remove_balance_dialog()


#     if is_logged_in():
#         logout_button(key="logout")
#     else:
#         open_login_page(key="login")

#     st.write("---")


# # Create a connection object
# conn = st.connection("gsheets", type=GSheetsConnection)


# # Function to load data from Google Sheets
# @st.cache_data(ttl="10s")
# def load_data():
#     return conn.read(worksheet="balances")


# # Refresh button
# if st.button("🔄 Refresh Data"):
#     st.cache_data.clear()

# # Load and display the data
# df = load_data()
# df["full_date"] = pd.to_datetime(df["full_date"], errors="coerce").dt.normalize()
# st.dataframe(df, use_container_width=True, hide_index=True)


# networth_over_time = df.groupby("full_date")["balance"].sum().reset_index()

# # Optional: Ensure full_date is a datetime object and sort
# networth_over_time["full_date"] = pd.to_datetime(networth_over_time["full_date"])
# networth_over_time = networth_over_time.sort_values("full_date")

# # Step 2: Create a minimal Plotly chart
# fig = go.Figure()

# fig.add_trace(
#     go.Scatter(
#         x=networth_over_time["full_date"],
#         y=networth_over_time["balance"],
#         mode="lines+markers",
#         name="Net Worth",
#         line=dict(color="royalblue", width=2),
#         marker=dict(size=4),
#     )
# )

# # Step 3: Update layout for minimal style with necessary labels
# fig.update_layout(
#     title="Net Worth Over Time",
#     xaxis_title="Date",
#     yaxis_title="Net Worth ($)",
#     template="simple_white",
#     margin=dict(l=40, r=40, t=50, b=40),
#     height=300,
# )

# # Display the chart
# col1, col2, col3 = st.columns([6, 2, 2])
# with col1:
#     st.plotly_chart(fig, use_container_width=True)
# with col2:
#     with st.container(border=True):
#         st.metric(
#             label="Latest Balance",
#             value=f"${networth_over_time['balance'].iloc[-1]:,.0f}",
#             delta=(
#                 f"{'-$' if networth_over_time['balance'].iloc[-1] - networth_over_time['balance'].iloc[-2] < 0 else '$'}"
#                 f"{abs(networth_over_time['balance'].iloc[-1] - networth_over_time['balance'].iloc[-2]):,.2f}"
#             ),
#         )
# with col3:
#     with st.container(border=True):
#         st.metric(
#             label="Total Entries",
#             value=f"{len(networth_over_time)}",
#             delta=None,  # No delta for total entries
#         )


# st.dataframe(networth_over_time, use_container_width=True, hide_index=True)


# latest = networth_over_time.iloc[networth_over_time["full_date"].idxmax()]
# prev = (
#     networth_over_time.iloc[networth_over_time["full_date"].idxmax() - 1]
#     if len(networth_over_time) > 1
#     else None
# )

# # Display the metric
# st.metric(
#     label=f"Net Worth as of {latest['full_date'].date()}",
#     value=f"${latest['balance']:,.2f}",
#     delta=(
#         f"{'-$' if latest['balance'] - prev['balance'] < 0 else '$'}{abs((latest['balance'] - prev['balance'])):,.2f}"
#         if prev is not None
#         else None
#     ),
# )


# import pandas as pd
# import numpy as np
# import streamlit as st

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
