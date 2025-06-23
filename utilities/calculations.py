from typing import Optional
from datetime import datetime
import pandas as pd


def calculate_age(
    from_date: datetime, to_date: datetime = datetime.today()
) -> float | None:
    """
    Calculate age in years between two dates.

    Parameters:
    - from_date (datetime): Beginning date
    - to_date (datetime): Ending date (default to today)

    Returns:
    - integer: years between two dates.
    """
    if not from_date or pd.isna(from_date):
        return None

    delta_days = (to_date - from_date).days
    age = delta_days / 365.25  # accounts for leap years
    return age


def calculate_target_networth(
    income: float,
    target_savings_rate: float,
    target_return_on_investment: float,
    age: Optional[datetime],
) -> Optional[float]:
    """
    Calculates target net worth based on user financial assumptions.

    Parameters:
    - income (float): Annual income.
    - target_savings_rate (float): Fraction of income saved monthly (e.g., 0.15).
    - target_return_on_investment (float): Annualized return rate (e.g., 0.07).
    - age (float): user's age.

    Returns:
    - float or None: The target net worth if all inputs are valid.
    """
    target_networth = (income / 12 * target_savings_rate) * (
        ((1 + (target_return_on_investment / 12)) ** ((age - 20) * 12))
        / (target_return_on_investment / 12)
        - 1 / (target_return_on_investment / 12)
    )

    return target_networth


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
