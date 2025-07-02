import pandas as pd
import numpy as np
import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from utilities.helper import get_config_value


def generate_balance_change_tables(conn, num_entries=6):
    """
    Generate raw summary DataFrames grouped by category from balance data.

    Returns:
        Tuple[pd.DataFrame, ...]: A tuple of unstyled DataFrames (one per category).
    """
    df = conn.read(worksheet="balances")
    df["full_date"] = pd.to_datetime(df["full_date"])
    df = df.sort_values("full_date")

    # Filter to the last N unique dates
    recent_dates = df["full_date"].drop_duplicates().sort_values().iloc[-num_entries:]
    df_filtered = df[df["full_date"].isin(recent_dates)]

    # Pivot balances
    pivot_df = (
        df_filtered.pivot_table(
            index=["category", "institution_name"],
            columns="full_date",
            values="balance",
            aggfunc="sum",
        )
        .sort_index(axis=1)
        .fillna(0)
    )

    # Format column names
    pivot_df.columns = [
        col.strftime("%Y-%m-%d") if isinstance(col, pd.Timestamp) else col
        for col in pivot_df.columns
    ]

    balance_columns = pivot_df.columns.tolist()

    # Calculate % changes
    last_vals = pivot_df[balance_columns[-1]]
    prev_vals = pivot_df[balance_columns[-2]]
    first_vals = pivot_df[balance_columns[0]]

    pivot_df["Last Change"] = (
        (last_vals - prev_vals) / prev_vals.replace(0, np.nan)
    ) * 100
    pivot_df["Change"] = (
        (last_vals - first_vals) / first_vals.replace(0, np.nan)
    ) * 100

    balance_columns = [
        col for col in pivot_df.columns if col not in ["Last Change", "Change"]
    ]
    pivot_df["Balance History"] = pivot_df[balance_columns].values.tolist()

    final_df = pivot_df.reset_index().fillna(0)

    # Split into per-category DataFrames with "Total" row added
    result_tables = []

    for category in final_df["category"].unique():
        df_cat = final_df[final_df["category"] == category].copy()
        numeric_data = df_cat[balance_columns].astype(float)
        totals = numeric_data.sum()

        last, prev, first = totals.iloc[-1], totals.iloc[-2], totals.iloc[0]
        delta_last = ((last - prev) / prev) * 100 if prev != 0 else 1
        delta_10 = ((last - first) / first) * 100 if first != 0 else 1

        total_row = {
            "category": "",
            "institution_name": "Total",
            "Last Change": delta_last,
            "Change": delta_10,
            "Balance History": totals.tolist(),
        }
        for i, col in enumerate(balance_columns):
            total_row[col] = totals.iloc[i]

        df_cat = pd.concat([df_cat, pd.DataFrame([total_row])], ignore_index=True)
        result_tables.append(df_cat)

    return tuple(result_tables)


def style_balance_change_tables(tables_tuple):
    """
    Apply conditional styling to a tuple of balance DataFrames.

    Returns:
        Tuple[Styler, ...]: A tuple of styled DataFrames.
    """

    styled_tables = []

    for table in tables_tuple:
        # Identify date columns for comparisons
        num_date_cols = [col for col in table.columns if col[:4].isdigit()]
        first_col, prev_col, last_col = (
            num_date_cols[0],
            num_date_cols[-2],
            num_date_cols[-1],
        )

        def highlight_change(row, col):
            first = row[first_col]
            prev = row[prev_col]
            last = row[last_col]
            val = row[col]

            if pd.isna(val):
                return ""

            improved = last >= (prev if col == "Last Change" else first)

            return (
                f"background-color: {get_config_value('theme.ColorPalette.green')}; color: #2c6a3a"
                if improved
                else f"background-color: {get_config_value('theme.ColorPalette.red')}; color: #76333c"
            )

        def style_table(df):
            style_df = pd.DataFrame("", index=df.index, columns=df.columns)

            for i in df.index:
                is_total = df.loc[i, "institution_name"] == "Total"
                for col in df.columns:
                    style = ""
                    if is_total:
                        style += f"background-color: {get_config_value('theme.ColorPalette.secondaryBackgroundColor')}; font-weight: bold;"
                    if col in ["Last Change", "Change"]:
                        style = highlight_change(df.loc[i], col)
                    style_df.at[i, col] = style.strip("; ")
            return style_df

        styled_df = table.style.apply(style_table, axis=None)
        styled_tables.append(styled_df)

    return tuple(styled_tables)


def balance_by_institution_over_time_tile(conn):
    """
    Handle all UI, user input, and rendering of styled balance change tables.
    """
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
                "Display recent balance trends by institution and category. "
                "Use the slider to adjust how many recent entries are included."
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
                selected_number_of_periods = st.slider(
                    label="Number of Previous Entries to Show",
                    min_value=3,
                    max_value=10,
                    value=8,
                )

        # === Pipeline Execution ===
        raw_tables = generate_balance_change_tables(
            conn, num_entries=selected_number_of_periods
        )
        styled_tables = style_balance_change_tables(raw_tables)

        # === Manual Rendering ===
        for raw_df, styled_df in zip(raw_tables, styled_tables):
            category_name = raw_df["category"].dropna().unique()[0] or "Summary"
            balance_columns = [col for col in raw_df.columns if col[:4].isdigit()]

            st.markdown(f"##### {category_name}")
            st.dataframe(
                styled_df,
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
                            format="dollar", help=f"Balance on {col}", width="small"
                        )
                        for col in balance_columns
                    },
                },
                hide_index=True,
                use_container_width=True,
            )
