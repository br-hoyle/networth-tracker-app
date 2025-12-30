import streamlit as st
from streamlit_gsheets import GSheetsConnection

from datetime import date, timedelta
import calendar

from streamlit_extras.stylable_container import stylable_container

from utilities.sidebar import show_app_sidebar
from utilities.gsheets import (
    refresh_connection,
    load_settings_to_session_state,
    settings_assumptions,
)

from pages.income_and_expenses.components.spreadsheet import transactions_spreadsheet
from pages.income_and_expenses.components.income_vs_expense import (
    plot_income_vs_expense,
)
from pages.income_and_expenses.components.expense_by_group_item import (
    display_group_and_item_trends,
)
from pages.income_and_expenses.components.expense_by_time_grp import (
    plot_spending_patterns,
)

from utilities.helper import *

# ----------------- HEADER ----------------- #
st.set_page_config(layout="wide", page_title="Income & Expenses")

view_type = show_app_sidebar()

# Initialize Connection & Check for Staleness
conn = st.connection("gsheets", type=GSheetsConnection)
load_settings_to_session_state(conn=conn)

header_cols = st.columns([7, 1, 1])
with header_cols[0]:
    st.title("Income & Expenses Dashboard")
with header_cols[1]:
    st.write("")
    st.write("")
    refresh_connection()
with header_cols[2]:
    st.write("")
    st.write("")
    if st.button("☰ Settings", type="secondary", use_container_width=True):
        settings_assumptions(conn=conn)

check_transactions_staleness(conn)

## ----------- BALANCES DASHBOARD ----------- ##
if view_type == "Dashboard":

    # Get ALL Transaction Data
    with st.spinner("Loading data..."):
        transactions_df = conn.read(worksheet="transactions")
        transactions_df["full_date"] = pd.to_datetime(transactions_df["full_date"])

    # Calculate the last day of the current month
    today = date.today()
    _, last_day = calendar.monthrange(today.year, today.month)
    current_month_end = date(today.year, today.month, last_day)

    # Calculate the start date (1 year minus the end date)
    one_year_ago_start = current_month_end - timedelta(days=365)

    # Update max_date for the widget constraints
    max_date = current_month_end
    min_date = transactions_df["full_date"].min().date()

    cols = st.columns([2, 1, 7])
    with cols[0]:
        date_range = st.date_input(
            "Date Range",
            value=(one_year_ago_start, current_month_end),
            min_value=min_date,
            max_value=max_date,
        )

    # Handle the case where the user has only clicked one date so far
    if len(date_range) == 2:
        st.session_state["start_date"] = date_range[0]
        st.session_state["end_date"] = date_range[1]
    with cols[1]:
        period = st.selectbox(
            "Select Time Period",
            ["week", "month", "quarter", "year"],
            index=1,
            format_func=lambda x: x.title(),
        )

    # Filter Transactions by Date Range
    filtered_transactions_df = transactions_df[
        (transactions_df["full_date"].dt.date >= st.session_state["start_date"])
        & (transactions_df["full_date"].dt.date <= st.session_state["end_date"])
    ]

    # ---------- KEY METRIC TILES ---------- #
    header_metrics_df = conn.query(
        """
        select
        sum(case when type = 'income' then amount else 0 end) as total_income,
        sum(case when type = 'expense' then amount else 0 end) as total_expenses,
        total_income + total_expenses as net_savings,
        net_savings / total_income * 100 as savings_rate
        from transactions
        group by month_yr
        order by month_yr desc
        limit 2
        """
    )
    # Calculate month-over-month differences
    diff_row = header_metrics_df.iloc[[0, 1]].diff().iloc[[1]] * -1
    header_metrics_df = pd.concat([header_metrics_df, diff_row], ignore_index=True)

    # Display Key Metrics
    key_metrics = ["Total Income", "Total Expenses", "Net Savings", "Savings Rate"]
    col1, col2, col3, col4 = st.columns(4)
    for col, metric in zip(
        [col1, col2, col3, col4],
        key_metrics,
    ):
        with col:
            with stylable_container(
                key=f"tile__{metric.lower().replace(' ', '_')}",
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
                st.markdown(f"##### {metric.replace('_', ' ').title()}")
                st.metric(
                    label="*Last Month*",
                    value=(
                        f"${header_metrics_df.at[0, metric.lower().replace(' ', '_')].astype(int):,.0f}"
                        if metric != "Savings Rate"
                        else f"{header_metrics_df.at[0, metric.lower().replace(' ', '_')]:.1f}%"
                    ),
                    delta=(
                        (
                            f"${header_metrics_df.at[2, metric.lower().replace(' ', '_')].astype(int):,.0f}"
                            if metric != "Savings Rate"
                            else f"{header_metrics_df.at[2, metric.lower().replace(' ', '_')]:.1f}%"
                        )
                        + " vs. previous month"
                    ),
                    delta_color="normal" if metric != "Total Expenses" else "inverse",
                )

    col1_size = st.slider(
        "Slider",
        min_value=1,
        max_value=99,
        value=50,
        step=1,
        key="spacer",
        format="",
        label_visibility="collapsed",
    )
    columns = st.columns([col1_size, 101 - col1_size])
    # INCOME vs EXPENSE by PERIOD
    with columns[0]:
        plot_income_vs_expense(conn, period)
    # DAILY / WEEKLY / MONTHLY SPENDING PATTERNS #
    with columns[1]:
        plot_spending_patterns(conn)

    # ---------- GROUP & ITEM TRENDS ---------- #
    display_group_and_item_trends(conn, period)


# ---------- TRANSACTIONS SPREADSHEET ---------- #
if view_type == "Spreadsheet":
    transactions_spreadsheet(conn)


render_footer()
