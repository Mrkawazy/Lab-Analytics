
import streamlit as st
import pandas as pd
import plotly.express as px

from ui.layout import app_header_with_logo, hide_streamlit_footer, render_footer, left_menu, sticky_right_panel_start
from ui.controls import upload_data, filters_panel
from analytics.tables import (
    organisms_counts, ast_table, antibiogram_matrix,
    clients_by_SIR, clients_by_patienttype, clients_by_ptype_and_SIR
)
from visuals.charts import bar_count, pie, histogram, heatmap_from_matrix, download_buttons
from analytics.helpers import age_to_years_for_analysis, add_age_bands_years

st.set_page_config(page_title="Dashboard — Lab Data Cleaner", layout="wide")
hide_streamlit_footer()

# Header with logo (top-left) and title on right
app_header_with_logo("app/assets/logo.png", "📊 Dashboard", "Clean → Filter → Analyze → Export")

# 3-column layout: left menu, center content, right filters
center, right = st.columns([6, 1], gap="large")

# with left:
#     left_menu([("📊 Dashboard", "pages/1_📊_Dashboard.py"),
#                ("ℹ️ About", "pages/2_ℹ️_About.py")])

with center:
    df = upload_data()
    if df is None:
        st.info("👋 Upload a CSV/Excel or tick **Use demo data** to start.")
        render_footer(brand="MOHCC Zimbabwe — HMIS", author="Obvious J. Kawanzaruwa (OJ)", links={"Email":"mailto:obviouscc@outlook.com"})
        st.stop()

with right:
    sticky_right_panel_start()
    df_f = filters_panel(df)

with center:
    # Downloads for cleaned dataset
    st.subheader("Download cleaned dataset")
    keep_only = st.checkbox("Keep only cleaned + key columns in download", value=True)
    if keep_only:
        cols_keep = [c for c in [
            'year_clean','patient_id_key','age_value','age_type','gender_clean',
            'patienttype_clean','sample_date_clean','specimen_clean','pathogen_clean',
            'antibiotic_clean','sir_clean','facility_clean','hcf_id_clean'
        ] if c in df.columns]
        out_df = df[cols_keep].copy()
    else:
        out_df = df.copy()

    st.download_button("⬇️ Cleaned CSV",
                       data=out_df.to_csv(index=False).encode("utf-8"),
                       file_name="cleaned_data.csv", mime="text/csv")

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    total_rows = len(df_f)
    total_patients = df_f['patient_id_key'].nunique() if 'patient_id_key' in df_f.columns else total_rows
    distinct_path = df_f['pathogen_clean'].nunique() if 'pathogen_clean' in df_f.columns else 0
    distinct_spec = df_f['specimen_clean'].nunique() if 'specimen_clean' in df_f.columns else 0
    k1.metric("Total occurrences (rows)", f"{total_rows:,}")
    k2.metric("Unique patients", f"{total_patients:,}")
    k3.metric("Pathogens", f"{distinct_path:,}")
    k4.metric("Specimen types", f"{distinct_spec:,}")

    tabs = st.tabs([
        "Overview","Demographics","Facilities","Organisms","AST Results","Antibiogram","Clients by SIR & Patient Type"
    ])

    with tabs[0]:
        c1, c2 = st.columns(2)
        if 'specimen_clean' in df_f.columns:
            sp = df_f['specimen_clean'].value_counts().reset_index()
            sp.columns = ['Specimen','Count']
            fig = bar_count(sp.head(15), x='Specimen', y='Count', title="Top Specimen")
            c1.plotly_chart(fig, use_container_width=True); download_buttons(fig, "top_specimen", c1)
        if 'pathogen_clean' in df_f.columns:
            pa = df_f['pathogen_clean'].value_counts().reset_index()
            pa.columns = ['Pathogen','Count']
            fig = bar_count(pa.head(15), x='Pathogen', y='Count', title="Top Pathogens")
            c2.plotly_chart(fig, use_container_width=True); download_buttons(fig, "top_pathogens", c2)

    with tabs[1]:
        if {'age_value','age_type'}.issubset(df_f.columns):
            tmp = df_f.copy()
            tmp['age_years'] = tmp.apply(age_to_years_for_analysis, axis=1)
            tmp = tmp.dropna(subset=['age_years'])
            tmp['age_band'] = add_age_bands_years(tmp['age_years'])
            fig = histogram(tmp, x='age_band', nbins=30, title="Age distribution (years)")
            st.plotly_chart(fig, use_container_width=True); download_buttons(fig, "age_distribution")
        if 'gender_clean' in df_f.columns and df_f['gender_clean'].notna().any():
            g = df_f['gender_clean'].value_counts().rename_axis('Gender').reset_index(name='Count')
            fig = pie(g, names='Gender', values='Count', title="Gender split")
            st.plotly_chart(fig, use_container_width=True); download_buttons(fig, "gender_split")

    with tabs[2]:
        if 'facility_clean' in df_f.columns and df_f['facility_clean'].notna().any():
            f = df_f['facility_clean'].value_counts().rename_axis('Facility').reset_index(name='Count')
            fig = bar_count(f, x='Facility', y='Count', title="Submissions by facility")
            st.plotly_chart(fig, use_container_width=True); download_buttons(fig, "facility_submissions")
            st.dataframe(f, use_container_width=True)
        if 'hcf_id_clean' in df_f.columns and df_f['hcf_id_clean'].notna().any():
            f2 = df_f['hcf_id_clean'].value_counts().rename_axis('HCF_ID').reset_index(name='Count')
            fig2 = bar_count(f2, x='HCF_ID', y='Count', title="Submissions by HCF_ID")
            st.plotly_chart(fig2, use_container_width=True); download_buttons(fig2, "hcf_submissions")
            st.dataframe(f2, use_container_width=True)

    with tabs[3]:
        if 'pathogen_clean' in df_f.columns:
            org = organisms_counts(df_f)
            st.dataframe(org, use_container_width=True)
            st.download_button("⬇️ Organisms CSV", data=org.to_csv(index=False).encode("utf-8"),
                               file_name="organisms_list.csv", mime="text/csv")
        else:
            st.info("No pathogen data.")

    with tabs[4]:
        ast = ast_table(df_f)
        if ast.empty:
            st.info("Need both antibiotic_clean and sir_clean.")
        else:
            st.dataframe(ast.head(200), use_container_width=True)
            st.download_button("⬇️ Interpreted AST CSV",
                               data=ast.to_csv(index=False).encode("utf-8"),
                               file_name="interpreted_ast_clean.csv", mime="text/csv")

    with tabs[5]:
        piv = antibiogram_matrix(df_f)
        if piv.empty:
            st.info("Need pathogen_clean, antibiotic_clean, sir_clean.")
        else:
            fig = heatmap_from_matrix(piv, "Antibiogram — % Susceptible")
            st.plotly_chart(fig, use_container_width=True); download_buttons(fig, "antibiogram_percentS")
            st.download_button("⬇️ Antibiogram matrix CSV",
                               data=piv.reset_index().to_csv(index=False).encode("utf-8"),
                               file_name="antibiogram_matrix.csv", mime="text/csv")

    with tabs[6]:
        by_sir = clients_by_SIR(df_f)
        if not by_sir.empty:
            fig = bar_count(by_sir, x='sir_clean', y='UniquePatients', title="Unique patients by SIR", textcol='UniquePatients')
            st.plotly_chart(fig, use_container_width=True); download_buttons(fig, "clients_by_SIR")
            st.download_button("⬇️ Table CSV (SIR)",
                               data=by_sir.to_csv(index=False).encode('utf-8'),
                               file_name="clients_by_SIR.csv", mime="text/csv")

        by_pt = clients_by_patienttype(df_f)
        if not by_pt.empty:
            fig2 = bar_count(by_pt, x='patienttype_clean', y='UniquePatients', title="Unique patients by Patient type", textcol='UniquePatients')
            st.plotly_chart(fig2, use_container_width=True); download_buttons(fig2, "clients_by_patienttype")
            st.download_button("⬇️ Table CSV (Patient type)",
                               data=by_pt.to_csv(index=False).encode('utf-8'),
                               file_name="clients_by_PatientType.csv", mime="text/csv")

        ctab = clients_by_ptype_and_SIR(df_f)
        if not ctab.empty:
            fig3 = px.bar(ctab, x='patienttype_clean', y='UniquePatients', color='sir_clean',
                          barmode='stack', title="Unique patients by Patient type × SIR", text='UniquePatients')
            fig3.update_traces(textposition='outside', cliponaxis=False)
            st.plotly_chart(fig3, use_container_width=True); download_buttons(fig3, "clients_by_ptype_and_SIR")
            st.download_button("⬇️ Table CSV (Patient type × SIR)",
                               data=ctab.to_csv(index=False).encode('utf-8'),
                               file_name="clients_by_PType_SIR.csv", mime="text/csv")

render_footer(brand="MOHCC Zimbabwe — HMIS", author="Obvious J. Kawanzaruwa (OJ)", links={"Email":"mailto:obviouscc@outlook.com"})
