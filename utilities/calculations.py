from typing import Optional
from datetime import datetime
import pandas as pd


def calculate_age(
    from_date: datetime, to_date: datetime = datetime.today()
) -> float | None:
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

    Args:
        income (float): Annual income.
        target_savings_rate (float): Fraction of income saved monthly (e.g., 0.15).
        target_return_on_investment (float): Annualized return rate (e.g., 0.07).
        birthdate (datetime): User's birthdate.

    Returns:
        float or None: The target net worth if all inputs are valid.
    """

    target_networth = (income / 12 * target_savings_rate) * (
        ((1 + (target_return_on_investment / 12)) ** ((age - 20) * 12))
        / (target_return_on_investment / 12)
        - 1 / (target_return_on_investment / 12)
    )

    return target_networth
