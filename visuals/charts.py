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
