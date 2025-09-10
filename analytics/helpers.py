import numpy as np
import pandas as pd

def age_to_years_for_analysis(row) -> float:
    v, t = row.get('age_value'), row.get('age_type')
    if pd.isna(v) or pd.isna(t): return np.nan
    t = str(t).lower()
    if t == 'years':  return float(v)
    if t == 'months': return float(v) / 12.0
    if t == 'weeks':  return float(v) * 7.0 / 365.25
    if t == 'days':   return float(v) / 365.25
    if t == 'hours':  return float(v) / (24.0 * 365.25)
    return np.nan

def add_age_bands_years(s_years: pd.Series) -> pd.Series:
    bins = [-0.01, 1, 5, 15, 25, 45, 65, 120]
    labels = ["<1y", "1–5y", "5–15y", "15–25y", "25–45y", "45–65y", "65+y"]
    return pd.cut(s_years, bins=bins, labels=labels)
