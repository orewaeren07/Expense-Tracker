"""Plotly charts for the Reports page."""
import plotly.express as px

from calculations import CURRENCY

PALETTE = ["#ef4444", "#f59e0b", "#3b82f6", "#8b5cf6",
           "#ec4899", "#14b8a6", "#84cc16", "#94a3b8"]


def _tidy(fig):
    fig.update_layout(margin=dict(l=8, r=8, t=8, b=8), height=360,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend_title_text="")
    return fig


def category_pie(breakdown):
    fig = px.pie(names=list(breakdown), values=list(breakdown.values()),
                 hole=0.5, color_discrete_sequence=PALETTE)
    fig.update_traces(textinfo="percent",
                      hovertemplate="%{label}: " + CURRENCY + "%{value:,.2f}<extra></extra>")
    return _tidy(fig)


def category_bar(breakdown):
    names = list(breakdown)
    fig = px.bar(x=names, y=list(breakdown.values()), color=names,
                 color_discrete_sequence=PALETTE)
    fig.update_traces(hovertemplate="%{x}: " + CURRENCY + "%{y:,.2f}<extra></extra>")
    fig.update_layout(showlegend=False, xaxis_title=None,
                      yaxis_title=f"Amount ({CURRENCY})")
    return _tidy(fig)
