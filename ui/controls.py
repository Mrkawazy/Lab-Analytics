
import pandas as pd
import streamlit as st
from data.pipeline import clean_data
from data.demo import get_demo_df


def multiselect_with_all(label: str, options: list, state_key: str,
                         default_all: bool = True, max_default: int = 15) -> list:
    """
    Renders: [All] checkbox + a multiselect.
    - If 'All' is checked: returns all options and disables the multiselect.
    - If 'All' is not checked: returns selected subset.
    Guarded against stale defaults that aren’t in the current options.
    """
    # Deduplicate and drop empty/None values
    options = [o for o in dict.fromkeys(options) if o not in (None, "", "NaN")]

    all_key = f"{state_key}_all"
    all_selected = st.session_state.get(all_key, default_all)

    col_all, col_ms = st.columns([1, 3])
    with col_all:
        all_selected = st.checkbox("All", value=all_selected, key=all_key)

    # Base default for first render (when no session state exists)
    base_default = options if default_all else options[:min(max_default, len(options))]

    # Pull any saved selection and SANITIZE it against current options
    session_default = st.session_state.get(state_key, base_default)
    session_default = [v for v in session_default if v in options]

    # If user ticked All, force default to all options so Streamlit never errors
    default_vals = options if all_selected else (session_default or base_default)

    with col_ms:
        sel = st.multiselect(
            label, options,
            default=default_vals,          # always a subset of options
            key=state_key,
            disabled=all_selected
        )

    return options if all_selected else sel


@st.cache_data(show_spinner=False)
def _clean_cached(df_raw: pd.DataFrame) -> pd.DataFrame:
    return clean_data(df_raw)

def upload_data():
    """Render an uploader in the main content area (center). Returns cleaned df or None."""
    with st.expander("📤 Upload data", expanded=True):
        file = st.file_uploader("CSV or Excel", type=["csv","xlsx","xls"], key="main_uploader")
        use_demo = st.checkbox("Use demo data", value=False, key="use_demo_center")

    if not file and not use_demo:
        return None

    # Load
    if use_demo:
        df_raw = get_demo_df()
    else:
        if file.name.lower().endswith((".xlsx",".xls")):
            df_raw = pd.read_excel(file)
        else:
            try:
                df_raw = pd.read_csv(file)
            except Exception:
                file.seek(0); df_raw = pd.read_csv(file, encoding='latin1')

    st.success(f"Loaded {len(df_raw):,} rows × {len(df_raw.columns)} columns")
    with st.expander("Preview: raw data", expanded=False):
        st.dataframe(df_raw.head(20), use_container_width=True)

    with st.spinner("Cleaning + completing patient fields..."):
        df = _clean_cached(df_raw)

    return df
def filters_panel(df: pd.DataFrame):
    if df is None:
        return None

    df_f = df.copy()
    st.subheader("Filters")

    # Year
    if 'year_clean' in df_f.columns and df_f['year_clean'].notna().any():
        years = sorted(df_f['year_clean'].dropna().unique().tolist())
        sel_years = multiselect_with_all("Year", years, "flt_years", default_all=True)
        if sel_years:
            df_f = df_f[df_f['year_clean'].isin(sel_years)]

    # HCF_ID
    if 'hcf_id_clean' in df_f.columns and df_f['hcf_id_clean'].notna().any():
        hcfs = sorted(df_f['hcf_id_clean'].dropna().unique().tolist())
        sel_hcf = multiselect_with_all("HCF_ID", hcfs, "flt_hcf", default_all=True)
        if sel_hcf:
            df_f = df_f[df_f['hcf_id_clean'].isin(sel_hcf)]

    # Facility
    if 'facility_clean' in df_f.columns and df_f['facility_clean'].notna().any():
        facs = sorted(df_f['facility_clean'].dropna().unique().tolist())
        sel_fac = multiselect_with_all("Facility", facs, "flt_fac", default_all=True)
        if sel_fac:
            df_f = df_f[df_f['facility_clean'].isin(sel_fac)]

    # Patient type
    if 'patienttype_clean' in df_f.columns and df_f['patienttype_clean'].notna().any():
        pts = sorted(df_f['patienttype_clean'].dropna().unique().tolist())
        sel_pt = multiselect_with_all("Patient type", pts, "flt_pt", default_all=True)
        if sel_pt:
            df_f = df_f[df_f['patienttype_clean'].isin(sel_pt)]

    # Specimen
    if 'specimen_clean' in df_f.columns and df_f['specimen_clean'].notna().any():
        specs = sorted(df_f['specimen_clean'].dropna().unique().tolist())
        sel_sp = multiselect_with_all("Specimen", specs, "flt_spec", default_all=True)
        if sel_sp:
            df_f = df_f[df_f['specimen_clean'].isin(sel_sp)]

    # NEW: Antibiotic
    if 'antibiotic_clean' in df_f.columns and df_f['antibiotic_clean'].notna().any():
        abx = sorted(df_f['antibiotic_clean'].dropna().unique().tolist())
        sel_abx = multiselect_with_all("Antibiotic", abx, "flt_abx", default_all=True)
        if sel_abx:
            df_f = df_f[df_f['antibiotic_clean'].isin(sel_abx)]

    # Gender
    if 'gender_clean' in df_f.columns and df_f['gender_clean'].notna().any():
        gens = sorted(df_f['gender_clean'].dropna().unique().tolist())
        sel_g = multiselect_with_all("Gender", gens, "flt_gender", default_all=True)
        if sel_g:
            df_f = df_f[df_f['gender_clean'].isin(sel_g)]

    return df_f
