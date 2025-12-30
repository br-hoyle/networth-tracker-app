import streamlit as st

from streamlit_extras.stylable_container import stylable_container
from streamlit_gsheets import GSheetsConnection

import plotly.graph_objects as go

from utilities.helper import get_config_value

import colorsys


def darken_color(hex_color, amount=0.2):
    """
    Darkens the given hex color by the specified amount (0 to 1).
    """
    hex_color = hex_color.lstrip("#")
    rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    # Convert RGB to HLS
    h, l, s = colorsys.rgb_to_hls(*[x / 255.0 for x in rgb])
    # Lower the 'Lightness' value
    darker_l = max(0, l - amount)
    # Convert back to RGB
    new_rgb = colorsys.hls_to_rgb(h, darker_l, s)
    return "#%02x%02x%02x" % tuple(int(x * 255) for x in new_rgb)


def plot_income_vs_expense(conn: GSheetsConnection, period: str):

    # GET DATA
    start_dt = st.session_state["start_date"]
    end_dt = st.session_state["end_date"]
    df = conn.query(
        f"""
        select
        {period+'_yr'} as period,
        sum(case when type = 'income' then amount else 0 end) as income,
        sum(case when type = 'expense' then -amount else 0 end) as expenses,
        sum(amount) as net
        from transactions
        where strptime(full_date, '%m/%d/%Y') BETWEEN '{start_dt}' AND '{end_dt}'
        group by period
        order by period
        """
    )

    with stylable_container(
        key=f"income_vs_expense_plot",
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
            st.markdown(f"#### Income vs Expenses by {period.title()}")
            st.caption(
                f"Displaying income and expenses between {start_dt} and {end_dt}"
            )

            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    name="Income",
                    x=df["period"],
                    y=df["income"],
                    marker_color=darken_color(
                        get_config_value("theme.ColorPalette.green"), 0.25
                    ),
                    marker_line=dict(
                        color=get_config_value("theme.ColorPalette.textColor"),
                        width=1,
                    ),
                )
            )

            fig.add_trace(
                go.Bar(
                    name="Expenses",
                    x=df["period"],
                    y=df["expenses"],
                    marker_color=darken_color(
                        get_config_value("theme.ColorPalette.red"), 0.15
                    ),
                    marker_line=dict(
                        color=get_config_value("theme.ColorPalette.textColor"),
                        width=1,
                    ),
                )
            )

            fig.add_trace(
                go.Scatter(
                    name="Net",
                    x=df["period"],
                    y=df["net"],
                    mode="lines+markers",
                    line=dict(
                        color=get_config_value("theme.ColorPalette.primaryColor"),
                        width=3,
                    ),
                    marker=dict(size=8),
                )
            )

            fig.update_layout(
                height=375,
                hovermode="x unified",
                template="simple_white",
                margin=dict(l=0, r=0, t=20, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                xaxis_title=period.title(),
                yaxis_title="Amount ($)",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False},
            )

            with st.expander("Show Data Table"):
                st.dataframe(df)
