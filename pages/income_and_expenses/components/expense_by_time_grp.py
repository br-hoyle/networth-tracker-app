import streamlit as st

import plotly.graph_objects as go

from streamlit_extras.stylable_container import stylable_container

from utilities.helper import get_config_value


def plot_spending_patterns(conn):
    with stylable_container(
        key=f"tile__spending_patterns",
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
        with st.container(height=575, border=False):
            cols = st.columns([7, 3])
            with cols[1]:
                period_grp = st.selectbox(
                    "Expenses by:",
                    ["Day of Week", "Week of Year", "Month of Year", "Quarter of Year"],
                    index=0,
                    key="expense_pattern_option",
                )
            with cols[0]:
                st.markdown(f"#### Spending Patterns by {period_grp.title()}")
                st.caption(
                    f"Displaying income and expenses between {st.session_state.start_date} and {st.session_state.end_date}"
                )
                st.space()

            # Map user input to (Generic Bucket, Unique Period ID)
            mapping = {
                "Day of Week": ("dow", "full_date"),
                "Week of Year": ("week", "week_of_yr"),
                "Month of Year": ("month_num", "month_yr"),
                "Quarter of Year": ("quarter", "quarter_yr"),
            }

            generic_bucket, unique_id = mapping[period_grp]

            df = conn.query(
                f"""
                    WITH period_totals AS (
                        -- Step 1: Sum everything for each specific instance in time
                        SELECT 
                            {generic_bucket} AS bucket,
                            {unique_id} AS period_id,
                            SUM(-amount) AS total_amount
                        FROM transactions
                        WHERE type = 'expense' -- Usually you'd filter for expenses for this analysis
                        GROUP BY 1, 2
                    )
                    -- Step 2: Average the totals of those specific instances
                    SELECT 
                        bucket as time_period,
                        AVG(total_amount) AS average_spend
                    FROM period_totals
                    GROUP BY 1
                    ORDER BY bucket
                    """
            )
            avg_value = df["average_spend"].mean()

            fig = go.Figure()

            # 3. Add the Bar chart (set to green)
            fig.add_trace(
                go.Bar(
                    x=df["time_period"],
                    y=df["average_spend"],
                    name="Spend",
                    marker_color=get_config_value("theme.ColorPalette.primaryColor"),
                    marker_line=dict(
                        width=1, color=get_config_value("theme.ColorPalette.textColor")
                    ),
                    text=df["average_spend"],
                    texttemplate="$%{text:,.2f}",
                    textposition="auto",
                )
            )

            # 4. Add the Average Line
            fig.add_trace(
                go.Scatter(
                    x=df["time_period"],
                    y=[avg_value] * len(df),
                    mode="lines",
                    name=f"Average: ${avg_value:,.2f}",
                    line=dict(
                        color=get_config_value("theme.ColorPalette.textColor"),
                        width=3,
                        dash="dash",
                    ),
                )
            )

            # 5. Finalize layout
            fig.update_layout(
                xaxis_title=period_grp,
                yaxis_title="Average Spend",
                yaxis=dict(range=[0, df["average_spend"].max()]),
                template="simple_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=20, b=0),
                height=350,
                showlegend=False,
            )

            # fig.update_layout(
            #     height=350,
            #     hovermode="x unified",
            #     template="simple_white",
            #     margin=dict(l=0, r=0, t=20, b=0),
            #     paper_bgcolor="rgba(0,0,0,0)",
            #     plot_bgcolor="rgba(0,0,0,0)",
            #     showlegend=False,
            #     xaxis_title=period.title(),
            # )

            st.plotly_chart(
                fig, use_container_width=True, config={"displayModeBar": False}
            )
            with st.expander("Show Table"):
                st.dataframe(
                    df,
                    column_config={
                        "time_period": st.column_config.TextColumn(period_grp),
                        "average_spend": st.column_config.NumberColumn(
                            "Average Spend", format="dollar"
                        ),
                    },
                    use_container_width=True,
                    hide_index=True,
                )
