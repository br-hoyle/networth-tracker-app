import streamlit as st
import pandas as pd

from streamlit_extras.stylable_container import stylable_container

from utilities.helper import get_config_value


def display_group_and_item_trends(conn, period: str):
    with stylable_container(
        key=f"tile__expense_trends",
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
        cols = st.columns([7, 1.5, 1.5])
        with cols[0]:
            st.markdown(f"#### Expenses Buckets by {period.title()}")
            st.caption(
                f"Displaying income and expenses between {st.session_state.start_date} and {st.session_state.end_date}"
            )
            st.space()

        with cols[1]:
            grouping_option = st.selectbox(
                "Group Expenses By:",
                ["Group", "Item"],
                index=0,
                key="expense_trend_grouping_option",
            )
            grouping_columns = (
                """ "group" as expense_grouping, item as expense_item, """
                if grouping_option == "Item"
                else """ "group" as expense_grouping, """
            )
        with cols[2]:
            selected_number_of_periods = st.slider(
                label="Last N-Periods to Show",
                min_value=3,
                max_value=24,
                value=6,
            )

        trends_by_group_item_df = conn.query(
            f"""
                select
                datetrunc('{period}', strptime(full_date, '%m/%d/%Y')) as period,
                {grouping_columns}
                SUM(-amount) as total_expense
                from transactions
                where type = 'expense'
                AND strptime(full_date, '%m/%d/%Y') BETWEEN '{st.session_state['start_date']}' AND '{st.session_state['end_date']}'
                group by period, expense_grouping {', expense_item' if grouping_option == "Item" else ''}
                order by period, total_expense desc
                """
        )
        trends_by_group_item_df = (
            pd.pivot(
                data=trends_by_group_item_df,
                columns=["period"],
                index=(
                    ["expense_grouping", "expense_item"]
                    if grouping_option == "Item"
                    else ["expense_grouping"]
                ),
                values="total_expense",
            )
            .fillna(0)
            .iloc[:, -selected_number_of_periods:]
        )

        # Format Date columns
        trends_by_group_item_df.columns = [
            col.strftime("%Y-%m-%d") if isinstance(col, pd.Timestamp) else col
            for col in trends_by_group_item_df.columns
        ]

        # Create list of balance columns
        balance_columns = trends_by_group_item_df.columns.tolist()

        # Create "Balance History" column for sparkline
        balance_columns = [
            col
            for col in trends_by_group_item_df.columns
            if col not in ["Average", "Median"]
        ]
        trends_by_group_item_df["Balance History"] = trends_by_group_item_df[
            balance_columns
        ].values.tolist()

        # Reset index for display
        final_df = trends_by_group_item_df.reset_index().fillna(0)

        # Print DataFrames
        def process_and_display_df(df, balance_cols, title=None):
            """Adds a total row, calculates stats, and displays a Streamlit dataframe."""
            if title:
                st.markdown(f"##### {title}")

            # Calculate Totals for numeric columns
            numeric_data = df[balance_cols].astype(float)
            totals = numeric_data.sum()

            # Build Total Row with "Balance History"
            total_row_data = {col: totals[col] for col in balance_cols}
            total_row_data.update(
                {
                    "expense_grouping": "Total",
                    "expense_item": "Total",
                    "Balance History": totals.values.tolist(),
                }
            )

            # Calculate Stats for the existing rows
            df["Average"] = df[balance_cols].mean(axis=1)
            df["Median"] = df[balance_cols].median(axis=1)

            # Combine existing rows (sorted) with the Total row
            full_df = pd.concat(
                [
                    df.sort_values(by="Average", ascending=False),
                    pd.DataFrame([total_row_data]),
                ],
                ignore_index=True,
            )

            # Recalculate Stats for the Total row specifically (so they aren't NaN)
            full_df["Average"] = full_df[balance_cols].mean(axis=1)
            full_df["Median"] = full_df[balance_cols].median(axis=1)

            # Drop rows that have a 0 average (i.e., no expenses in the period)
            full_df = full_df.loc[full_df["Average"] != 0.0, :]

            # Styling Logic
            def style_table(df):
                # Create an empty DataFrame of the same shape with no styles
                style_df = pd.DataFrame("", index=df.index, columns=df.columns)

                bg_color = get_config_value(
                    "theme.ColorPalette.secondaryBackgroundColor"
                )

                for i in df.index:
                    # Check if this row is the Total row
                    if df.loc[i, "expense_item"] == "Total":
                        style_df.loc[i, :] = (
                            f"background-color: {bg_color}; font-weight: bold;"
                        )
                return style_df

            styled_df = full_df.style.apply(style_table, axis=None)

            st.dataframe(
                styled_df,
                column_order=(
                    [
                        (
                            "expense_grouping"
                            if grouping_option == "Group"
                            else "expense_item"
                        )
                    ]
                    + balance_cols
                    + ["Balance History", "Average", "Median"]
                ),
                column_config={
                    "expense_grouping": st.column_config.TextColumn("Group"),
                    "expense_item": st.column_config.TextColumn("Item"),
                    **{
                        col: st.column_config.NumberColumn(
                            format="dollar", help=f"Balance on {col}", width="small"
                        )
                        for col in balance_columns
                    },
                    "Balance History": st.column_config.AreaChartColumn(
                        "Expense Over Time",
                        y_min=0,
                    ),
                    "Average": st.column_config.NumberColumn(format="dollar"),
                    "Median": st.column_config.NumberColumn(format="dollar"),
                },
                use_container_width=True,
                hide_index=True,
            )

        # --- Main Logic ---
        if grouping_option == "Item":
            for grp in final_df["expense_grouping"].unique():
                grp_df = final_df[final_df["expense_grouping"] == grp]
                process_and_display_df(grp_df, balance_columns, title=grp)
        else:
            # Treat the whole DF as one group
            final_df["expense_item"] = " "
            process_and_display_df(final_df, balance_columns)
