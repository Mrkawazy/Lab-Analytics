import streamlit as st
from ui.layout import app_header_with_logo, hide_streamlit_footer, render_footer

st.set_page_config(page_title="Lab Data Cleaner & Dashboard", layout="wide")
hide_streamlit_footer()

app_header_with_logo("app/assets/logo.png", "🧪 Lab Data Cleaner & Dashboard", "Use the left menu and right filters on Dashboard")

st.markdown("""
**Welcome:**  
This app seeks to simplify lab data analytics and reporting.
""")
st.markdown("""
**Navigation:**  
- Left column shows a logo and quick menu.  
- Open **📊 Dashboard** to upload and analyze data.  
- **Filters** are on the right panel within Dashboard.  
""")
render_footer(brand="MOHCC Zimbabwe — HMIS", author="Obvious J. Kawanzaruwa (OJ)", links={"Email":"mailto:obviouscc@outlook.com"})
