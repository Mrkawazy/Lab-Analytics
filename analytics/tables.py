import pandas as pd
import io


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


# import your cleaner from data/cleaners.py
try:
    from data.cleaners import clean_specimen
except Exception:  # small fallback if import path differs during dev
    def clean_specimen(val):
        import re
        if val is None: return "Other"
        v = str(val).strip().lower().replace("_"," ").replace("-"," ")
        v = re.sub(r"\s+", " ", v)
        if "blood" in v: return "Blood"
        if "urine" in v: return "Urine"
        if "stool" in v or "faec" in v or "fec" in v: return "Stool"
        if "csf" in v: return "CSF"
        if "genital" in v: return "Genital swab"
        if "sputum" in v or "trache" in v or "bronch" in v or "lower resp" in v: return "Lower respiratory (unspecified)"
        if "pus" in v or "wound" in v or "swab" in v: return "Pus"
        return "Other"

# Fixed categories → how they should appear in indicators
_CATS = [
    ("Blood",  "Blood samples"),
    ("Urine",  "Urine samples"),
    ("Stool",  "Stool samples"),
    ("CSF",    "CSF samples"),
    ("Genital swab", "Genital swab samples"),
    ("Lower respiratory (unspecified)", "Lower respiratory tract"),
    ("Pus",    "Pus swab samples"),
    ("Other",  "Other samples (Fluids)"),
]

def _spec_category(series: pd.Series) -> pd.Series:
    """Normalize raw specimen values into fixed indicator categories."""
    s = series.astype("string").map(clean_specimen)
    known = {k for k, _ in _CATS[:-1]}  # all except 'Other'
    return s.where(s.isin(list(known)), "Other")

def indicator_samples_table(
    df: pd.DataFrame,
    specimen_col: str = "specimen_clean",
    pathogen_col: str = "pathogen_clean",
) -> pd.DataFrame:
    """
    Build indicator rows:
      - SAMPHH1 (+ SAMPHH1.1..1.8): total samples by category
      - SAMPHH2 (+ SAMPHH2.1..2.8): positive cultures by category

    Positivity rule (default): pathogen_clean is present and not blank/'Unknown'/'unk'.
    Adjust by passing a different `pathogen_col` or precomputing a boolean and swapping the rule below.
    """
    if specimen_col not in df.columns:
        return pd.DataFrame(columns=["Indicator Code", "Indicator Description", "Number"])

    tmp = df.copy()
    tmp["__spec_cat"] = _spec_category(tmp[specimen_col])

    # --- positivity mask ---
    if pathogen_col in tmp.columns:
        p = tmp[pathogen_col].astype("string").str.strip().str.lower()
        pos = p.notna() & (p != "") & (~p.isin({"unknown", "unk"}))
    else:
        pos = pd.Series(False, index=tmp.index)

    order_keys = [k for k, _ in _CATS]
    counts_all = tmp["__spec_cat"].value_counts().reindex(order_keys, fill_value=0)
    counts_pos = tmp.loc[pos, "__spec_cat"].value_counts().reindex(order_keys, fill_value=0)

    # --- assemble rows ---
    rows = []
    # SAMPHH1 total
    rows.append(["SAMPHH1", "Total Number of samples collected from Human subjects", int(counts_all.sum())])
    # SAMPHH1.1..1.8
    for i, (key, desc) in enumerate(_CATS, start=1):
        child = desc if desc.endswith("samples") or "tract" in desc else f"{desc} samples"
        rows.append([f"SAMPHH1.{i}", child, int(counts_all[key])])

    # SAMPHH2 total
    rows.append(["SAMPHH2", "Total Number of samples collected from Human subjects which yielded positive cultures", int(counts_pos.sum())])
    # SAMPHH2.1..2.8
    for i, (key, desc) in enumerate(_CATS, start=1):
        rows.append([f"SAMPHH2.{i}", f"Number of {desc.lower()} which yielded positive culture", int(counts_pos[key])])

    return pd.DataFrame(rows, columns=["Indicator Code", "Indicator Description", "Number"])

__all__ = ["indicator_samples_table"]

# analytics/analytics.py
import pandas as pd
from typing import Optional, List

def bug_drug_sir_table(
    df: pd.DataFrame,
    pathogen_col: str = "pathogen_clean",
    specimen_col: str = "specimen_clean",
    antibiotic_col: str = "antibiotic_clean",
    sir_col: str = "sir_clean",
    *,
    # set these to use unique-patient counting
    patient_col: Optional[str] = None,
    count_unique_patients: bool = False,
    # display controls
    min_total: int = 0,
    percent_decimals: int = 1,
    sort_by: Optional[List[str]] = None,
    ascending: Optional[List[bool]] = None,
) -> pd.DataFrame:
    """
    Build a tidy table: Bug × Specimen × Antibiotic with S/I/R counts, Total, %S, %I, %R.

    Parameters
    ----------
    df : DataFrame
        Your (filtered) data.
    pathogen_col, specimen_col, antibiotic_col, sir_col : str
        Column names for pathogen, specimen, antibiotic, and S/I/R result.
    patient_col : Optional[str]
        Column with patient ID if counting unique patients.
    count_unique_patients : bool
        If True and patient_col provided, counts nunique(patient_col) per (bug, specimen, antibiotic, S/I/R)
        instead of row counts.
    min_total : int
        Drop rows with Total < min_total.
    percent_decimals : int
        Decimals for %S/%I/%R rounding.
    sort_by : list[str] | None
        Columns to sort by (default: ["Pathogen","Sample Type","Antimicrobial","Total"]).
    ascending : list[bool] | None
        Sort orders matching sort_by (default: [True, True, True, False]).

    Returns
    -------
    DataFrame with columns:
        Pathogen | Sample Type | Antimicrobial | S | I | R | Total | %S | %I | %R
    """
    needed = [pathogen_col, specimen_col, antibiotic_col, sir_col]
    extra = [patient_col] if (count_unique_patients and patient_col) else []
    data = df[ [c for c in needed + extra if c in df.columns] ].copy()

    # Keep only S/I/R
    data = data[data[sir_col].isin(["S", "I", "R"])]

    # Drop rows missing bug/specimen/antibiotic (can't classify)
    data = data.dropna(subset=[c for c in [pathogen_col, specimen_col, antibiotic_col] if c in data.columns])

    # Aggregate
    if count_unique_patients and patient_col and patient_col in data.columns:
        grouped = (
            data.groupby([pathogen_col, specimen_col, antibiotic_col, sir_col])[patient_col]
                .nunique()
        )
    else:
        grouped = (
            data.groupby([pathogen_col, specimen_col, antibiotic_col, sir_col])
                .size()
        )

    # Pivot S/I/R to columns
    g = grouped.unstack(sir_col, fill_value=0)

    # Ensure S/I/R columns exist even if empty
    for c in ("S", "I", "R"):
        if c not in g.columns:
            g[c] = 0

    # Totals and percentages
    g["Total"] = g[["S", "I", "R"]].sum(axis=1)
    if min_total > 0:
        g = g[g["Total"] >= min_total]

    denom = g["Total"].replace(0, pd.NA)
    g["%S"] = (g["S"] / denom * 100).round(percent_decimals)
    g["%I"] = (g["I"] / denom * 100).round(percent_decimals)
    g["%R"] = (g["R"] / denom * 100).round(percent_decimals)

    # Flatten and pretty column names
    out = (
        g.reset_index()
         .rename(columns={
             pathogen_col: "Pathogen",
             specimen_col: "Sample Type",
             antibiotic_col: "Antimicrobial"
         })
    )

    # Default sort
    if sort_by is None:
        sort_by = ["Pathogen", "Sample Type", "Antimicrobial", "Total"]
    if ascending is None:
        ascending = [True, True, True, False]

    out = out.sort_values(sort_by, ascending=ascending, na_position="last").reset_index(drop=True)
    return out
