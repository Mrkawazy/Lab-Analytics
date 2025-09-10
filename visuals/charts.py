import plotly.express as px
import streamlit as st
import kaleido

def download_buttons(fig, base_name: str, container=None):
    area = container if container is not None else st
    png_bytes = None
    try:
        png_bytes = fig.to_image(format="png", scale=2)  # requires kaleido
    except Exception:
        png_bytes = None
    html_bytes = fig.to_html(include_plotlyjs='cdn', full_html=True).encode('utf-8')
    if png_bytes is not None:
        area.download_button("📥 PNG", data=png_bytes, file_name=f"{base_name}.png", mime="image/png")
    else:
        area.caption("PNG export requires the 'kaleido' package. Skipping PNG button.")
    area.download_button("📥 HTML", data=html_bytes, file_name=f"{base_name}.html", mime="text/html")

def bar_count(df, x, y, title, textcol='Count'):
    fig = px.bar(df, x=x, y=y, title=title, text=textcol)
    fig.update_traces(textposition='outside', cliponaxis=False)
    return fig

def pie(df, names, values, title):
    fig = px.pie(df, names=names, values=values, title=title)
    fig.update_traces(textinfo='label+percent+value')
    return fig

def histogram(df, x, nbins, title):
    fig = px.histogram(df, x=x, nbins=nbins, title=title)
    fig.update_traces(texttemplate='%{y}', textposition='outside')
    return fig


def heatmap_from_matrix(piv, title):
    return px.imshow(piv, aspect='auto', text_auto=True, origin='upper', title=title)

import pandas as pd
import plotly.express as px

def stacked_100(
    df: pd.DataFrame,
    x: str,                  # categorical on X (e.g., "age_band_5y")
    stack: str,              # stack/category to color by (e.g., "sex")
    y: str | None = None,    # numeric column to aggregate; if None, uses counts
    agg: str = "sum",        # aggregation for y when provided: "sum", "mean", etc.
    x_order: list[str] | None = None,   # optional fixed order for X
    stack_order: list[str] | None = None,  # optional fixed order for stack
    title: str | None = None,
    labels: dict | None = None,         # axis/legend labels
    dropna: bool = True,                # drop rows with NA in x/stack
):
    """
    Create a 100% stacked bar chart (share within each X category).

    - If `y` is None, it will count rows per (x, stack).
    - If `y` is given, it will aggregate `y` with `agg` per (x, stack).
    - Normalized to percent via Plotly's barnorm='percent'.
    """
    g = df.copy()

    # Drop NA in core fields if requested
    subset = [x, stack] + ([y] if y else [])
    if dropna:
        g = g.dropna(subset=subset)

    # Ordering
    if x_order is None:
        # Keep natural order by appearance
        x_order = list(pd.Index(g[x]).astype("string").dropna().unique())
    if stack_order is None:
        stack_order = list(pd.Index(g[stack]).astype("string").dropna().unique())

    # Group & aggregate
    if y is None:
        data = (
            g.groupby([x, stack])
             .size()
             .reset_index(name="value")
        )
        y_label = "Count"
    else:
        data = (
            g.groupby([x, stack], as_index=False)
             .agg(value=(y, agg))
        )
        y_label = y if labels is None else labels.get(y, y)

    # Build figure
    fig = px.bar(
        data, x=x, y="value", color=stack,
        barnorm="percent",                     # 100% stacked
        category_orders={x: x_order, stack: stack_order},
        title=title or f"{x} by {stack} (100% Stacked)",
        labels={(labels or {}) | {x: x, "value": "Share", stack: stack}}
    )
    fig.update_layout(
        barmode="stack",
        yaxis_title="Percent",
        xaxis_title=x,
        yaxis_ticksuffix="%",
        legend_title=stack
    )
    fig.update_traces(texttemplate="%{y:.0f}%", textposition="inside")
    return fig
