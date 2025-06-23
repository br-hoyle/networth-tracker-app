import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
from streamlit_extras.stylable_container import stylable_container

from utilities.gsheets import load_worksheet

from utilities.calculations import *


def future_value(principal: float, annual_rate: float, years: int) -> float:
    """
    Calculate the future value of a lump sum invested over time.

    Parameters:
    - principal: Initial investment amount
    - annual_rate: Annual interest rate (as a decimal, e.g. 0.07 for 7%)
    - years: Number of years the money is invested

    Returns:
    - Future value of the investment
    """
    return principal * (1 + annual_rate) ** years


def future_value_of_payments(
    payment: float, annual_rate: float, years: int, payments_per_year: int = 1
) -> float:
    """
    Calculate the future value of recurring payments (ordinary annuity).

    Parameters:
    - payment: Amount contributed each period
    - annual_rate: Annual interest rate (decimal)
    - years: Number of years contributions are made
    - payments_per_year: Number of payments per year (default is 1)

    Returns:
    - Future value of the payment stream
    """
    r = (1 + annual_rate) ** (1 / 12) - 1
    n = years * payments_per_year
    return payment * (((1 + r) ** n - 1) / r)


def present_value(future_value: float, annual_rate: float, years: int) -> float:
    """
    Calculate the present value of a future amount.

    Parameters:
    - future_value: Amount you want in the future
    - annual_rate: Annual discount rate (decimal)
    - years: Number of years until the amount is received

    Returns:
    - Present value needed today
    """
    return future_value / ((1 + annual_rate) ** years)


@st.dialog("Retirement Margin", width="large")
def retirement_margin__dialog(df: pd.DataFrame):

    latest = df.loc[df["full_date"].idxmax()]

    # Extract key values
    retirement_egg_fv = latest["retirement_egg__fv"]
    retirement_egg_cv = latest["retirement_egg__cv"]
    current_investments_fv = latest["current_investments__fv"]
    additional_investments_fv = latest["additional_investments__fv"]
    target_cv = latest["financial_independence_target__cv"]
    margin_cv = latest["retirment_margin__cv"]
    estimated_income_cv = latest["est_income_in_retirement__cv"]

    # Write summary
    st.write(
        f"""
        Based on your current trajectory, you're projected to have a retirement nest egg of **${retirement_egg_fv:,.0f}** in future dollars. This amount is built from two key components:\n
        
        * The future value of your current investments: **${current_investments_fv:,.0f}**  
        * The future value of additional investments you plan to make: **${additional_investments_fv:,.0f}**

        The present value of this is **${retirement_egg_cv:,.0f}**, and you'll need an estimated **{target_cv:,.0f}** *(current value)*.
        
        * This gives you an estimated retirement income of **${estimated_income_cv:,.0f}**, in today’s dollars.
        """
    )
    st.write("---")
    st.caption("All dollar values are displayed in the present value.")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_order=[
            "full_date",
            "total_investments",
            "retirement_egg__cv",
            "financial_independence_target__cv",
            "retirment_margin__cv",
            "est_income_in_retirement__cv",
        ],
        column_config={
            "full_date": st.column_config.DateColumn("Date"),
            "total_investments": st.column_config.NumberColumn(
                "Investments",
                format="dollar",
            ),
            "retirement_egg__cv": st.column_config.NumberColumn(
                "Total Retirement",
                help="Current Value of Current Investments and Additional Investments until Retirement.",
                format="dollar",
            ),
            "financial_independence_target__cv": st.column_config.NumberColumn(
                "Target Retirement",
                format="dollar",
            ),
            "retirment_margin__cv": st.column_config.NumberColumn(
                "Margin",
                help="Difference between Target Retirement and Estimated Retirement Nest Egg.",
                format="dollar",
            ),
            "est_income_in_retirement__cv": st.column_config.NumberColumn(
                "Retirement Income",
                help="Retirement income from Investments.",
                format="dollar",
            ),
        },
    )

    # --- Download Button ---
    st.download_button(
        label="Download",
        data=df.to_csv(index=False),
        icon=":material/download:",
        file_name="retirement_gap.csv",
    )


def retirement_margin_tile(conn: GSheetsConnection):

    ## LOAD
    df = conn.query(
        "select full_date, sum(case when category = 'Investments' then balance end) as total_investments from balances group by full_date;"
    )
    df["full_date"] = pd.to_datetime(df["full_date"])
    df = df.sort_values(by=["full_date"]).reset_index(drop=True)

    df["age"] = df["full_date"].apply(
        lambda date: calculate_age(
            from_date=st.session_state["birthdate"], to_date=date
        )
    )

    income_df = conn.read(worksheet="income")
    income_df["effective_start_date"] = pd.to_datetime(
        income_df["effective_start_date"]
    )
    income_df["effective_end_date"] = pd.to_datetime(
        income_df["effective_end_date"], errors="coerce"
    ).fillna(datetime.today())
    df["total_income"] = df["full_date"].apply(
        lambda date: income_df[
            (income_df["effective_start_date"] <= date)
            & (income_df["effective_end_date"] >= date)
        ]["income"].sum()
    )

    df["financial_independence_target__cv"] = (
        df["total_income"] * st.session_state["replacement_income_rate"]
    ) / 0.04

    df["years_to_retirement"] = st.session_state["target_retirement_age"] - df["age"]

    df["current_investments__fv"] = df.apply(
        lambda row: future_value(
            row["total_investments"],
            st.session_state["target_return_on_investment"],
            row["years_to_retirement"],
        ),
        axis=1,
    )

    df["additional_investments__fv"] = df.apply(
        lambda row: future_value_of_payments(
            payment=(row["total_income"] * st.session_state["target_savings_rate"])
            / 12,
            annual_rate=st.session_state["target_return_on_investment"],
            years=row["years_to_retirement"],
            payments_per_year=12,
        ),
        axis=1,
    )

    df["retirement_egg__fv"] = (
        df["current_investments__fv"] + df["additional_investments__fv"]
    )

    df["financial_independence_target__fv"] = df.apply(
        lambda row: future_value(
            row["financial_independence_target__cv"],
            st.session_state["inflation_rate"],
            row["years_to_retirement"],
        ),
        axis=1,
    )

    df["retirement_margin__fv"] = (
        df["retirement_egg__fv"] - df["financial_independence_target__fv"]
    )

    df["retirment_margin__cv"] = df.apply(
        lambda row: present_value(
            future_value=row["retirement_margin__fv"],
            annual_rate=st.session_state["inflation_rate"],
            years=row["years_to_retirement"],
        ),
        axis=1,
    )

    df["retirement_egg__cv"] = df.apply(
        lambda row: present_value(
            future_value=row["retirement_egg__fv"],
            annual_rate=st.session_state["inflation_rate"],
            years=row["years_to_retirement"],
        ),
        axis=1,
    )

    df["est_income_in_retirement__cv"] = df["retirement_egg__cv"] * 0.04

    ## CREATE TILE
    with stylable_container(
        key="retirement_margin",
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

        retirement_margin = df.loc[df["full_date"].idxmax(), "retirment_margin__cv"]

        progress = (
            df.loc[df["full_date"].idxmax(), "retirement_egg__cv"]
            / df.loc[df["full_date"].idxmax(), "financial_independence_target__cv"]
        )

        ## DISPLAY
        titlecols = st.columns([7, 3])
        with titlecols[0]:
            st.markdown("##### Retirement Margin")
        with titlecols[1]:
            if st.button("☰ View", use_container_width=True, key="retirement_margin"):
                retirement_margin__dialog(df=df)
        st.metric(
            "Retirement Margin",
            value=f"${retirement_margin:,.0f}",
            label_visibility="collapsed",
        )
        st.progress(
            value=np.minimum(progress, 1),
            text=f"Percent to Target: **{progress*100:.1f}%**",
        )
