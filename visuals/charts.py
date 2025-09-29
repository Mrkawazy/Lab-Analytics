import plotly.express as px
import streamlit as st
import kaleido
import pandas as pd
from pandas.api.types import is_numeric_dtype
import plotly.express as px

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

# def histogram(df, x, nbins, title):
#     fig = px.histogram(df, x=x, nbins=nbins, title=title)
#     fig.update_traces(texttemplate='%{y}', textposition='outside')
#     return fig

def histogram(df, x, nbins=30, title="", sort="none", custom_order=None):
    """
    sort: "none" | "count_desc" | "count_asc" | "alpha_asc" | "alpha_desc" | "custom"
    custom_order: list of category labels for x (used when sort="custom")
    """
    g = df.copy()

    # Handle categorical sorting
    if x in g.columns and not is_numeric_dtype(g[x]):
        s = g[x].astype("string").fillna("Unknown")
        g[x] = s  # ensure plotted values match order calc

        if sort == "count_desc":
            order = s.value_counts().index.tolist()
        elif sort == "count_asc":
            order = s.value_counts(ascending=True).index.tolist()
        elif sort == "alpha_asc":
            order = sorted(s.dropna().unique().tolist())
        elif sort == "alpha_desc":
            order = sorted(s.dropna().unique().tolist(), reverse=True)
        elif sort == "custom" and custom_order:
            order = list(custom_order)
        else:
            order = None
    else:
        order = None  # numeric: keep default bin order

    fig = px.histogram(g, x=x, nbins=nbins, title=title)
    fig.update_traces(texttemplate='%{y}', textposition='outside')

    if order:
        fig.update_xaxes(categoryorder="array", categoryarray=order)

    # Improve readability a bit
    fig.update_layout(uniformtext_minsize=10, uniformtext_mode="hide", bargap=0.05)
    return fig


def heatmap_from_matrix(piv, title):
    return px.imshow(piv, aspect='auto', text_auto=True, origin='upper', title=title)

import pandas as pd
import plotly.express as px

def stacked_100(
    df: pd.DataFrame,
    x: str,
    stack: str = None,
    y: str = None,          # backwards-compat; if provided, we treat it as `stack`
    value: str = None,      # numeric column to sum; if None we count rows
    title: str = "100% Stacked"
):
    # allow old signature stacked_100(df, x='...', y='category')
    if stack is None and y is not None:
        stack = y
    if stack is None:
        raise ValueError("Provide the `stack` column (the category to stack).")

    g = df.copy()

    # aggregate: either counts or sum of a numeric `value`
    if value is None:
        agg = (
            g.groupby([x, stack], dropna=False)
             .size()
             .reset_index(name="n")
        )
    else:
        agg = (
            g.groupby([x, stack], dropna=False)[value]
             .sum()
             .reset_index(name="n")
        )

    # percent within each x
    totals = agg.groupby(x)["n"].transform("sum")
    agg["pct"] = agg["n"] / totals * 100

    # tidy labels
    x_label = x.replace("_", " ").title()
    stack_label = stack.replace("_", " ").title()

    fig = px.bar(
        agg,
        x=x,
        y="pct",
        color=stack,
        barmode="stack",
        title=title,
        labels={"pct": "Percent", x: x_label, stack: stack_label},
        category_orders={x: sorted(agg[x].dropna().unique().tolist())}
    )
    fig.update_traces(text=agg["pct"].round(1).astype(str) + "%", textposition="inside")
    fig.update_layout(yaxis=dict(ticksuffix="%"), bargap=0.15, legend_title=stack_label)
    return fig
