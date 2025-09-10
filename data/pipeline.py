import re
import numpy as np
import pandas as pd
from .cleaners import (
    clean_year, parse_age, clean_gender, clean_patienttype, clean_specimen,
    clean_pathogen, clean_antibiotic, clean_sir
)

def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [re.sub(r"\s+", "_", c.strip()).lower() for c in df.columns]
    return df

def pick_col(df: pd.DataFrame, candidates):
    cols = set(df.columns)
    for c in candidates:
        if c in cols:
            return c
    return None

def _first_nonnull(s: pd.Series):
    nonnull = s.dropna()
    return nonnull.iloc[0] if not nonnull.empty else np.nan

def complete_patient_fields(df: pd.DataFrame) -> pd.DataFrame:
    if 'patient_id_key' not in df.columns:
        return df
    df = df.copy()
    grp = df.groupby('patient_id_key', dropna=False)
    cat_cols = [c for c in [
        'gender_clean','patienttype_clean','specimen_clean','pathogen_clean',
        'facility_clean','hcf_id_clean','sir_clean','age_type'
    ] if c in df.columns]
    num_cols = [c for c in ['age_value','year_clean'] if c in df.columns]
    for c in cat_cols:
        firsts = grp[c].transform(_first_nonnull)
        df[c] = df[c].fillna(firsts)
        df[c] = grp[c].transform(lambda s: s.ffill().bfill())
    for c in num_cols:
        firsts = grp[c].transform(_first_nonnull)
        df[c] = df[c].fillna(firsts)
        df[c] = grp[c].transform(lambda s: s.ffill().bfill())
    for c in ['gender_clean','patienttype_clean','sir_clean','facility_clean','hcf_id_clean','age_type','specimen_clean','pathogen_clean']:
        if c in df.columns:
            df[c] = df[c].fillna('Unknown')
    return df

def clean_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = normalize_cols(df_raw)
    col_year       = pick_col(df, ['year'])
    col_age        = pick_col(df, ['age','age_value'])
    col_gender     = pick_col(df, ['gender','sex'])
    col_ptype      = pick_col(df, ['patienttype','patient_type'])
    col_spec       = pick_col(df, ['specimen'])
    col_path       = pick_col(df, ['pathogen','organism'])
    col_abx        = pick_col(df, ['antibiotic','antibiotics','ab'])
    col_sir        = pick_col(df, ['sir','resultmicsir','resultzonesir','resultetestsir'])
    col_pid        = pick_col(df, ['patient_id','patientid','pid'])
    col_sampledate = pick_col(df, ['sample_date','dateofhospitalisation_visit','date','collection_date'])
    col_facility   = pick_col(df, ['facility','hospital','site','location','clinic','ward'])
    col_hcf_id     = pick_col(df, ['hcf_id','hcfid','facility_id','site_id','hospital_id'])

    if col_year: df['year_clean'] = df[col_year].apply(clean_year).astype('Int64')
    if col_age:
        ages = df[col_age].apply(parse_age)
        df['age_value'], df['age_type'] = zip(*ages)
    if col_gender: df['gender_clean'] = df[col_gender].apply(clean_gender)
    if col_ptype:  df['patienttype_clean'] = df[col_ptype].apply(clean_patienttype)
    if col_spec:   df['specimen_clean'] = df[col_spec].apply(clean_specimen)
    if col_path:   df['pathogen_clean'] = df[col_path].apply(clean_pathogen)
    if col_abx:    df['antibiotic_clean'] = df[col_abx].apply(clean_antibiotic)
    if col_sir:    df['sir_clean'] = df[col_sir].apply(clean_sir)
    if col_sampledate:
        df['sample_date_clean'] = pd.to_datetime(df[col_sampledate], errors='coerce', dayfirst=True)
    if col_pid: df['patient_id_key'] = df[col_pid].astype(str).str.strip()
    if col_facility: df['facility_clean'] = df[col_facility].astype(str).str.strip().replace({'': np.nan})
    if col_hcf_id:  df['hcf_id_clean'] = df[col_hcf_id].astype(str).str.strip().replace({'': np.nan})

    df = complete_patient_fields(df)
    return df
