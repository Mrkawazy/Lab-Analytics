import streamlit as st
from ui.layout import page_header, hide_streamlit_footer, render_footer

st.set_page_config(page_title="About — Lab Data Cleaner", layout="wide")
page_header("ℹ️ About this app", "MOHCC Zimbabwe — HMIS")
hide_streamlit_footer()

st.markdown("""
**Lab Data Cleaner & Dashboard** helps you:

- Clean and standardize lab/AMR files (patients, SIR, antibiotics, pathogens, specimen, HCF_ID).
- Filter by Year, Facility, HCF_ID, Patient type, Specimen, Gender.
- Analyze KPIs, Organisms list, AST results, Antibiogram, and Clients by SIR & Patient type.
- Export cleaned data and per-chart PNG/HTML files.

**How to use**
1. Go to the **📊 Dashboard** page.
2. Use the **sidebar** to **Upload** a CSV/Excel or tick **Use demo data**.
3. Apply **Filters** in the sidebar.
4. Explore the tabs and download outputs.
""")

st.info("For support or feature requests, contact OJ at obviouscc@outlook.com.")

render_footer(brand="MOHCC Zimbabwe — HMIS", author="Obvious J. Kawanzaruwa (OJ)", links={"Email":"mailto:obviouscc@outlook.com"})
