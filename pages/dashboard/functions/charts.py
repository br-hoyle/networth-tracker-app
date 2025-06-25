import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utilities.helper import *


def networth__chart(df: pd.DataFrame):
    # Line chart
    fig = go.Figure()

    # Trace with solid fill
    fig.add_trace(
        go.Scatter(
            x=df["full_date"],
            y=df["networth"],
            mode="lines",
            name="Net Worth",
            fill="tozeroy",
            fillcolor=get_config_value("theme.ColorPalette.primaryColor"),
            line=dict(
                color=get_config_value("theme.ColorPalette.primaryColor"),
                width=2,
            ),
            marker=dict(size=4),
            hovertemplate=(
                "<b>Date:</b> %{x|%b %d, %Y}<br>"
                "<b>Net Worth:</b> $%{y:,.2f}<extra></extra>"
            ),
        )
    )

    # Layout with clean formatting
    fig.update_layout(
        title="",
        xaxis=dict(
            showgrid=False,
            showline=False,  # No axis line
            zeroline=True,
            zerolinecolor=get_config_value("theme.ColorPalette.textColor"),
            zerolinewidth=1,
            tickfont=dict(color=get_config_value("theme.ColorPalette.textColor")),
            titlefont=dict(color=get_config_value("theme.ColorPalette.textColor")),
            fixedrange=True,
            constrain="domain",
            range=[
                df["full_date"].min(),
                df["full_date"].max(),
            ],
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            zeroline=True,
            zerolinecolor=get_config_value("theme.ColorPalette.primaryColor"),
            zerolinewidth=1,
            tickfont=dict(color=get_config_value("theme.ColorPalette.textColor")),
            titlefont=dict(color=get_config_value("theme.ColorPalette.textColor")),
            fixedrange=True,
            constrain="domain",
            range=[
                0,
                df["networth"].max() * 1.02,
            ],
        ),
        template="simple_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=20, b=0),
        height=235,
    )
    return fig


def percent_to_target__chart(
    df: pd.DataFrame,
):
    fig = go.Figure()

    # Trace: Percent to Target
    fig.add_trace(
        go.Scatter(
            x=df["full_date"],
            y=df["percent_to_target"],
            fill="tozeroy",
            fillcolor=get_config_value("theme.ColorPalette.primaryColor"),
            mode="lines",
            name="Percent to Target",
            line=dict(color=get_config_value("theme.ColorPalette.primaryColor")),
            hovertemplate=(
                "<b>Date:</b> %{x|%b %d, %Y}<br>"
                "<b>Percent to Target:</b> %{y:.2%}<extra></extra>"
            ),
        )
    )

    # Trace: Horizontal target line at 100%
    x_range = pd.date_range(
        start=df["full_date"].min(),
        end=df["full_date"].max(),
        periods=200,
    )

    fig.add_trace(
        go.Scatter(
            x=x_range,
            y=[1.0] * len(x_range),
            mode="lines",
            name="Target (100%)",
            line=dict(
                color=get_config_value("theme.ColorPalette.textColor"),
                dash="dash",
            ),
            hovertemplate=(
                "<b>Date:</b> %{x|%b %d, %Y}<br>"
                "<b>Target:</b> %{y:.2%}<extra></extra>"
            ),
        )
    )

    # Layout with clean formatting
    fig.update_layout(
        title="",
        height=250,
        template="simple_white",
        showlegend=False,
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            tickfont=dict(color=get_config_value("theme.ColorPalette.textColor")),
            titlefont=dict(color=get_config_value("theme.ColorPalette.textColor")),
            showgrid=False,
            showline=False,
            zeroline=True,
            zerolinecolor=get_config_value("theme.ColorPalette.primaryColor"),
            zerolinewidth=1,
            fixedrange=True,
            constrain="domain",
            range=[
                df["full_date"].min(),
                df["full_date"].max(),
            ],
        ),
        yaxis=dict(
            title="Percent to Target",
            tickformat=".0%",
            tickfont=dict(color=get_config_value("theme.ColorPalette.textColor")),
            titlefont=dict(color=get_config_value("theme.ColorPalette.textColor")),
            showgrid=False,
            showline=False,
            zeroline=True,
            zerolinecolor=get_config_value("theme.ColorPalette.primaryColor"),
            zerolinewidth=1,
            fixedrange=True,
            constrain="domain",
        ),
    )

    return fig
