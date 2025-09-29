
import streamlit as st
import pandas as pd
import plotly.express as px
import io


from ui.layout import app_header_with_logo, hide_streamlit_footer, render_footer, left_menu, sticky_right_panel_start
from ui.controls import upload_data, filters_panel
from analytics.tables import (
    organisms_counts, ast_table, antibiogram_matrix,
    clients_by_SIR, clients_by_patienttype, clients_by_ptype_and_SIR,
    indicator_samples_table,bug_drug_sir_table
)
from visuals.charts import *
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
        "Overview","Demographics","Facilities","Organisms","AST Results","Antibiogram",
        "Clients by SIR & Patient Type","Repeat Tests","Indicators","SIR by Bug & Specimen"
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
        # ---- Build patient-level view (matches total_patients) ----
        d = df_f.copy()
        if 'sample_date_clean' in d.columns:
            d['__dt'] = pd.to_datetime(d['sample_date_clean'], errors='coerce')
            d = d.sort_values('__dt', ascending=False)  # prefer latest record per patient
        df_pat = d.dropna(subset=['patient_id_key']).drop_duplicates('patient_id_key', keep='first')

        # (Optional) sanity check:
        # assert df_pat['patient_id_key'].nunique() == total_patients

        # ---- Age distribution & Age×Sex based on unique patients ----
        if {'age_value','age_type'}.issubset(df_pat.columns):
            p = df_pat.copy()
            p['age_years'] = p.apply(age_to_years_for_analysis, axis=1)
            p = p.dropna(subset=['age_years'])
            p['age_band'] = add_age_bands_years(p['age_years'])

                        # Sort controls (front-end)
            sort_choice = st.selectbox(
                "Sort age bands",
                ["Natural (band order)", "Count (high→low)", "Count (low→high)", "A→Z", "Z→A"],
                index=0,
            )

            # Map UI choice -> histogram()'s sort param
            sort_map = {
                "Natural (band order)": "none",
                "Count (high→low)": "count_desc",
                "Count (low→high)": "count_asc",
                "A→Z": "alpha_asc",
                "Z→A": "alpha_desc",
            }
            sort_param = sort_map[sort_choice]

            # Plot using the user's choice
            fig = histogram(p, x="age_band", nbins=30, title="Age distribution (unique patients)", sort=sort_param)

            st.plotly_chart(fig, use_container_width=True); download_buttons(fig, "age_distribution_unique")

            if 'gender_clean' in p.columns:
                fig2 = stacked_100(p, x='age_band', stack="gender_clean", title="Age × Sex (unique patients)")
                st.plotly_chart(fig2, use_container_width=True); download_buttons(fig2, "age_sex_unique")

        # ---- Gender split based on unique patients ----
        if 'gender_clean' in df_pat.columns and df_pat['gender_clean'].notna().any():
            g = df_pat['gender_clean'].value_counts().rename_axis('Gender').reset_index(name='UniquePatients')
            fig3 = pie(g, names='Gender', values='UniquePatients', title="Gender split (unique patients)")
            st.plotly_chart(fig3, use_container_width=True); download_buttons(fig3, "gender_split_unique")

        # clean temp
        df_f.drop(columns=['__dt'], inplace=True, errors='ignore')

        # if {'age_value','age_type','gender_clean'}.issubset(df_f.columns):
        #     tmp = df_f.copy()
        #     tmp['age_years'] = tmp.apply(age_to_years_for_analysis, axis=1)
        #     tmp = tmp.dropna(subset=['age_years'])
        #     tmp['age_band'] = add_age_bands_years(tmp['age_years'])
        #     fig = histogram(tmp, x='age_band', nbins=30, title="Age distribution (years)")
        #     st.plotly_chart(fig, use_container_width=True); download_buttons(fig, "age_distribution")
        #     fig2=stacked_100(tmp,x='age_band',stack="gender_clean",title="Age and Sex")
        #     st.plotly_chart(fig2, use_container_width=True); download_buttons(fig2, "Age and Sex")
           
        # if 'gender_clean' in df_f.columns and df_f['gender_clean'].notna().any():
        #     g = df_f['gender_clean'].value_counts().rename_axis('Gender').reset_index(name='Count')
        #     fig = pie(g, names='Gender', values='Count', title="Gender split")
        #     st.plotly_chart(fig, use_container_width=True); download_buttons(fig, "gender_split")

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
    with tabs[7]:  # "Repeat Visits"
        st.subheader("🔁 Clients with Repeat Tests (same patient, different sample dates)")

        required = {'patient_id_key', 'sample_date_clean'}
        optional = ['specimen_clean', 'pathogen_clean', 'sir_clean', 'facility_clean', 'hcf_id_clean']

        if not required.issubset(df_f.columns):
            missing = ", ".join(sorted(required - set(df_f.columns)))
            st.info(f"Need columns present: {', '.join(sorted(required))}. Missing: {missing}")
        else:
            desired_cols = ['patient_id_key', 'sample_date_clean', *optional]
            tmp = df_f.reindex(columns=desired_cols).copy()

            # Keep as datetime64[ns] (NO .dt.date here)
            tmp['sample_date_clean'] = pd.to_datetime(tmp['sample_date_clean'], errors='coerce')

            # Drop rows without a patient id
            tmp = tmp.dropna(subset=['patient_id_key'])

            g = tmp.groupby('patient_id_key', dropna=False)
            agg = g.agg(
                total_rows=('sample_date_clean', 'size'),
                # Count distinct calendar days; normalize removes time portion
                distinct_sample_dates=('sample_date_clean', lambda s: s.dropna().dt.normalize().nunique()),
                first_sample_date=('sample_date_clean', 'min'),
                last_sample_date=('sample_date_clean', 'max')
            ).reset_index()

            # Convert display columns to plain date AFTER agg
            for c in ['first_sample_date', 'last_sample_date']:
                agg[c] = agg[c].dt.date

            repeats = agg.loc[agg['distinct_sample_dates'] > 1] \
                        .sort_values(['distinct_sample_dates', 'last_sample_date'], ascending=[False, False])

            c1, c2 = st.columns(2)
            c1.metric("Patients with repeat tests", f"{len(repeats):,}")
            c2.metric("All unique patients (filtered)", f"{tmp['patient_id_key'].nunique():,}")

            if repeats.empty:
                st.success("No repeat tests found under current filters.")
            else:
                st.caption("Summary — one row per patient with >1 distinct sample dates")
                st.dataframe(repeats, use_container_width=True)
                st.download_button(
                    "⬇️ Download repeat-tests summary (CSV)",
                    data=repeats.to_csv(index=False).encode('utf-8'),
                    file_name="repeat_tests_summary.csv",
                    mime="text/csv"
                )

                # Detailed rows for flagged patients
                detail_cols = ['patient_id_key', 'sample_date_clean', *optional]
                details = tmp[tmp['patient_id_key'].isin(repeats['patient_id_key'])] \
                            .reindex(columns=detail_cols) \
                            .sort_values(['patient_id_key', 'sample_date_clean'])
                # Convert datetime to date for display/export
                if 'sample_date_clean' in details.columns:
                    details['sample_date_clean'] = details['sample_date_clean'].dt.date

                st.caption("Detail — all samples for patients with repeat tests")
                st.dataframe(details, use_container_width=True)
                st.download_button(
                    "⬇️ Download detailed rows (CSV)",
                    data=details.to_csv(index=False).encode('utf-8'),
                    file_name="repeat_tests_details.csv",
                    mime="text/csv"
                )
    # ----- Inside your page (e.g., a new tab "Indicators") -----
    with tabs[8]:
        st.subheader("📋 Indicator Summary — Samples & Positive Cultures")

        ind = indicator_samples_table(df_f)  # from analytics.tables
        if ind.empty:
            st.info("No indicator data available.")
        else:
            # 1) Main indicator table
            st.dataframe(ind, use_container_width=True)

            # CSV download (main)
            st.download_button(
                "⬇️ Download indicators (CSV)",
                data=ind.to_csv(index=False).encode("utf-8"),
                file_name="lab_indicators.csv",
                mime="text/csv",
                key="dl_ind_csv",
            )

            # 2) Build a compact breakdown table from SAMPHH1.* and SAMPHH2.* rows
            c1 = ind[ind["Indicator Code"].str.fullmatch(r"SAMPHH1\.\d+")].copy()
            c2 = ind[ind["Indicator Code"].str.fullmatch(r"SAMPHH2\.\d+")].copy()

            if not c1.empty and not c2.empty:
                c1["idx"] = c1["Indicator Code"].str.extract(r"SAMPHH1\.(\d+)").astype(int)
                c2["idx"] = c2["Indicator Code"].str.extract(r"SAMPHH2\.(\d+)").astype(int)

                brk = (
                    c1[["idx", "Indicator Description", "Number"]]
                    .merge(c2[["idx", "Number"]], on="idx", suffixes=("_Total", "_Positive"))
                    .rename(columns={
                        "Indicator Description": "Specimen Category",
                        "Number_Total": "Total",
                        "Number_Positive": "Positive",
                    })
                    .drop(columns=["idx"])
                )
                brk["% Positive"] = (brk["Positive"] / brk["Total"]).replace([pd.NA, float("inf")], 0).fillna(0) * 100
                brk["% Positive"] = brk["% Positive"].round(1)

                st.markdown("**Breakdown by specimen category**")
                st.dataframe(brk, use_container_width=True)

                # CSV download (breakdown)
                st.download_button(
                    "⬇️ Download breakdown (CSV)",
                    data=brk.to_csv(index=False).encode("utf-8"),
                    file_name="lab_indicators_breakdown.csv",
                    mime="text/csv",
                    key="dl_brk_csv",
                )

                # 3) Excel download with both sheets
                # Excel download with both sheets
                buf = io.BytesIO()
                try:
                    with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
                        ind.to_excel(xw, index=False, sheet_name="Indicators")
                        brk.to_excel(xw, index=False, sheet_name="Breakdown")
                except Exception:
                    # fallback to default engine (e.g., openpyxl)
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf) as xw:
                        ind.to_excel(xw, index=False, sheet_name="Indicators")
                        brk.to_excel(xw, index=False, sheet_name="Breakdown")
                buf.seek(0)

                st.download_button(
                    "⬇️ Download Excel (Indicators + Breakdown)",
                    data=buf.getvalue(),
                    file_name="lab_indicators.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_xlsx",
                )

            else:
                st.info("Insufficient detail rows to build breakdown (need SAMPHH1.* and SAMPHH2.*).")
    with tabs[9]:
        st.subheader("🐞 Bug × Specimen × Antibiotic — Counts & %S/%I/%R")

        # Toggle: count rows vs unique patients
        use_unique = st.checkbox("Count unique patients (not rows)", value=False)

        tbl = bug_drug_sir_table(
            df_f,
            patient_col="patient_id_key",
            count_unique_patients=use_unique,
            min_total=0,            # set e.g. 10 to hide low-n cells
            percent_decimals=1
        )

        # Simple sort control (optional)
        sort_field = st.selectbox("Sort by", ["Pathogen","Sample Type","Antimicrobial","Total","%S","%R"], index=3)
        asc = st.checkbox("Ascending", value=False)
        tbl = tbl.sort_values(sort_field, ascending=asc, na_position="last")

        st.dataframe(tbl, use_container_width=True)

        st.download_button(
            "⬇️ Download Bug–Drug table (CSV)",
            data=tbl.to_csv(index=False).encode("utf-8"),
            file_name="bug_drug_SIR_table.csv",
            mime="text/csv",
        )

        import io
        buf = io.BytesIO()
        with pd.ExcelWriter(buf) as xw:
            tbl.to_excel(xw, index=False, sheet_name="Bug-Drug SIR")
        buf.seek(0)
        st.download_button(
            "⬇️ Download Excel (Bug–Drug SIR)",
            data=buf.getvalue(),
            file_name="bug_drug_SIR_table.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
render_footer(brand="MOHCC Zimbabwe — HMIS", author="Obvious J. Kawanzaruwa (OJ)", links={"Email":"mailto:obviouscc@outlook.com"})
