import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from streamlit_extras.stylable_container import stylable_container

from streamlit_gsheets import GSheetsConnection
from utilities.helper import get_config_value


def balance_by_group_tile(conn: GSheetsConnection):
    # --- Hardcoded Colors ---
    color_map = {
        # Investments
        "Investments": "#bb5a38",  # primaryColor
        "Roth 401K": "#d08a6c",
        "Roth IRA": "#d09e89",
        "Brokerage": "#d6ae9d",  # slightly lighter warm tone
        "Traditional IRA": "#e2ccc3",
        "Health Savings Account": "#c9b3a9",
        # Home
        "Home": "#3d3a2a",  # textColor - dark neutral
        "Home Equity": "#7c7563",  # warm neutral mid-tone
        # Banking
        "Banking": "#8a8175",  # soft brownish-gray
        "Checking": "#c7c1b4",  # desaturated tan/gray
        "Savings": "#b8b2a6",
        "Credit": "#f6cc98",
    }

    # --- UI Container ---
    with stylable_container(
        key="bottom_tile",
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
        # --- Data ---
        df = conn.query(
            """
            SELECT
                full_date, 
                category, 
                CASE WHEN category = 'Home' THEN 'Home Equity' ELSE account_type END AS account_group, 
                SUM(balance) AS total_balance
            FROM balances
            GROUP BY full_date, category, account_group
            ORDER BY full_date, category, account_group;
            """
        )
        df["full_date"] = pd.to_datetime(df["full_date"])

        # --- Controls ---
        cols_top = st.columns([8, 1.25, 1.25])
        with cols_top[0]:
            st.markdown("### Balance by Group")

        with cols_top[1]:
            selected_group = st.selectbox(
                "Group by:", options=["Category", "Account Type"], index=0
            )

        with cols_top[2]:
            selected_filltrace = st.toggle("Fill Traces", value=True)
            selected_stacktrace = (
                st.toggle("Stack Traces", value=True) if selected_filltrace else False
            )

        # --- Aggregates ---
        df_category = (
            df.groupby(["full_date", "category"])["total_balance"].sum().reset_index()
        )
        df_account_group = (
            df.groupby(["full_date", "account_group"])["total_balance"]
            .sum()
            .reset_index()
        )

        chart_df = df_category if selected_group == "Category" else df_account_group
        group_col = "category" if selected_group == "Category" else "account_group"

        # --- Chart Columns ---
        cols_chart = st.columns([4, 0.5, 6])

        # --- Time Series Chart ---
        with cols_chart[2]:
            fig = go.Figure()
            for group_value in chart_df[group_col].unique():
                group_data = chart_df[chart_df[group_col] == group_value]
                fill = (
                    "tozeroy"
                    if selected_filltrace and not selected_stacktrace
                    else None
                )
                stack = "one" if selected_filltrace and selected_stacktrace else None

                # Plot main colored line on top
                fig.add_trace(
                    go.Scatter(
                        x=group_data["full_date"],
                        y=group_data["total_balance"],
                        mode="lines",  # include markers to apply outline
                        name=group_value,
                        fill=fill,
                        fillcolor=color_map.get(group_value, "#cccccc"),
                        stackgroup=stack,
                        line=dict(
                            color=color_map.get(group_value, "#cccccc"),
                            width=2,
                        ),
                    )
                )

            fig.update_layout(
                height=350,
                hovermode="x unified",
                template="simple_white",
                margin=dict(l=0, r=0, t=20, b=0),
                legend_title=selected_group,
                xaxis=dict(
                    tickfont=dict(
                        color=get_config_value("theme.ColorPalette.textColor")
                    ),
                    showgrid=False,
                    showline=False,
                    zeroline=True,
                    zerolinecolor=get_config_value("theme.ColorPalette.primaryColor"),
                    zerolinewidth=1,
                    fixedrange=True,
                    constrain="domain",
                    range=[df["full_date"].min(), df["full_date"].max()],
                ),
                yaxis=dict(
                    tickformat="$,.0f",
                    tickfont=dict(
                        color=get_config_value("theme.ColorPalette.textColor")
                    ),
                    showgrid=False,
                    showline=False,
                    zeroline=True,
                    zerolinecolor=get_config_value("theme.ColorPalette.primaryColor"),
                    zerolinewidth=1,
                    fixedrange=True,
                    constrain="domain",
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(
                fig, use_container_width=True, config={"displayModeBar": False}
            )

        with cols_chart[1]:
            st.markdown(
                f"""
    <style>
        .divider-vertical-line {{
            border-left: 2px solid #9f8770;
            height: 320px;
            margin: auto;
        }}
    </style>
    <div class="divider-vertical-line"></div>
    """,
                unsafe_allow_html=True,
            )

        # --- Sunburst Chart ---
        with cols_chart[0]:
            latest_date = df["full_date"].max()
            latest_df = df[df["full_date"] == latest_date]

            sunburst_data = (
                latest_df.groupby(["category", "account_group"])["total_balance"]
                .sum()
                .reset_index()
            )

            traces = []
            for account in sunburst_data["account_group"].unique():
                sub_df = sunburst_data[sunburst_data["account_group"] == account]
                group = sub_df["category"].iloc[0]

                traces.append(
                    go.Bar(
                        x=sub_df["category"],
                        y=sub_df["total_balance"],
                        name=account,
                        # Grouping
                        legendgroup=group,
                        legendgrouptitle_text=(
                            group
                            if not any(t["legendgroup"] == group for t in traces)
                            else None
                        ),
                        marker_color=color_map.get(account, None),
                        text=[
                            f"{account} <br> ${bal/1000:.1f}K"
                            for bal in sub_df["total_balance"]
                        ],
                        cliponaxis=False,
                    )
                )

            # Step 3: Create the figure
            fig = go.Figure(data=traces)

            # Step 4: Layout
            fig.update_layout(
                barmode="stack",
                height=350,
                template="simple_white",
                margin=dict(l=0, r=50, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                bargap=0.1,
                bargroupgap=0.0,
                showlegend=False,
                yaxis=dict(
                    tickformat="$,.0f",
                    tickfont=dict(
                        color=get_config_value("theme.ColorPalette.textColor")
                    ),
                    showgrid=False,
                    showline=False,
                    zeroline=True,
                    zerolinewidth=0,
                    fixedrange=True,
                    constrain="domain",
                ),
                xaxis=dict(
                    tickfont=dict(
                        color=get_config_value("theme.ColorPalette.textColor")
                    ),
                    showgrid=False,
                    showline=False,
                    zeroline=False,
                    zerolinewidth=0,
                    fixedrange=False,
                ),
            )
            st.plotly_chart(
                fig, use_container_width=True, config={"displayModeBar": False}
            )
