import pandas as pd

def organisms_counts(df_f: pd.DataFrame) -> pd.DataFrame:
    org = (df_f['pathogen_clean'].value_counts(dropna=True)
           .rename_axis('Pathogen').reset_index(name='Count'))
    org['Percent'] = (org['Count'] / org['Count'].sum() * 100).round(2)
    return org

def ast_table(df_f: pd.DataFrame) -> pd.DataFrame:
    needed = {'antibiotic_clean','sir_clean'}
    if not needed.issubset(df_f.columns):
        return pd.DataFrame()
    cols = [c for c in [
        'sample_date_clean','year_clean','hcf_id_clean','facility_clean','patient_id_key',
        'specimen_clean','pathogen_clean','antibiotic_clean','sir_clean'
    ] if c in df_f.columns]
    return df_f.dropna(subset=list(needed))[cols].copy()

def antibiogram_matrix(df_f: pd.DataFrame) -> pd.DataFrame:
    need = {'pathogen_clean','antibiotic_clean','sir_clean'}
    if not need.issubset(df_f.columns):
        return pd.DataFrame()
    base = (df_f.dropna(subset=['pathogen_clean','antibiotic_clean','sir_clean'])
                .groupby(['pathogen_clean','antibiotic_clean','sir_clean']).size()
                .reset_index(name='n'))
    totals = base.groupby(['pathogen_clean','antibiotic_clean'])['n'].sum().rename('total')
    base = base.merge(totals, on=['pathogen_clean','antibiotic_clean'])
    base['pct'] = base['n'] / base['total'] * 100
    s = base[base['sir_clean']=='S']
    piv = s.pivot(index='pathogen_clean', columns='antibiotic_clean', values='pct').fillna(0).round(1)
    return piv

def clients_by_SIR(df_f: pd.DataFrame) -> pd.DataFrame:
    id_col = 'patient_id_key' if 'patient_id_key' in df_f.columns else None
    if 'sir_clean' not in df_f.columns: return pd.DataFrame()
    g = df_f.dropna(subset=['sir_clean']).groupby('sir_clean')
    if id_col:
        return g[id_col].nunique().reset_index(name='UniquePatients')
    return g.size().reset_index(name='UniquePatients')

def clients_by_patienttype(df_f: pd.DataFrame) -> pd.DataFrame:
    id_col = 'patient_id_key' if 'patient_id_key' in df_f.columns else None
    if 'patienttype_clean' not in df_f.columns: return pd.DataFrame()
    g = df_f.dropna(subset=['patienttype_clean']).groupby('patienttype_clean')
    if id_col:
        return g[id_col].nunique().reset_index(name='UniquePatients')
    return g.size().reset_index(name='UniquePatients')

def clients_by_ptype_and_SIR(df_f: pd.DataFrame) -> pd.DataFrame:
    id_col = 'patient_id_key' if 'patient_id_key' in df_f.columns else None
    need = {'sir_clean','patienttype_clean'}
    if not need.issubset(df_f.columns): return pd.DataFrame()
    g = df_f.dropna(subset=list(need)).groupby(['patienttype_clean','sir_clean'])
    if id_col:
        return g[id_col].nunique().reset_index(name='UniquePatients')
    return g.size().reset_index(name='UniquePatients')
