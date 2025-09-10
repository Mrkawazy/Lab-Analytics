import re
import pandas as pd
import numpy as np

ABX_MAP = {
    'ampicillin':'Ampicillin','amp':'Ampicillin',
    'amoxicillin':'Amoxicillin',
    'amoxicillin clavulanic acid':'Amoxicillin-clavulanate',
    'amoxicillin-clavulanic acid':'Amoxicillin-clavulanate',
    'augmentin':'Amoxicillin-clavulanate','augumentin':'Amoxicillin-clavulanate',
    'amc':'Amoxicillin-clavulanate','aug':'Amoxicillin-clavulanate',
    'penicillin':'Penicillin','pen':'Penicillin',
    'penicillin g':'Penicillin G','pg':'Penicillin G',
    'oxacillin':'Oxacillin','oxa':'Oxacillin','ox':'Oxacillin',
    'cloxacillin':'Cloxacillin',
    'ceftriaxone':'Ceftriaxone','ceftriazone':'Ceftriaxone','cerftriazone':'Ceftriaxone','ctr':'Ceftriaxone','cro':'Ceftriaxone',
    'cefotaxime':'Cefotaxime','ctx':'Cefotaxime',
    'ceftazidime':'Ceftazidime','caz':'Ceftazidime',
    'cefepime':'Cefepime','cefepime fep':'Cefepime','fep':'Cefepime','cpm':'Cefepime',
    'cefuroxime':'Cefuroxime','cxn':'Cefuroxime',
    'cefoxitin':'Cefoxitin','fox':'Cefoxitin',
    'cefixime':'Cefixime','cfm':'Cefixime',
    'cefpirome':'Cefpirome','cpo':'Cefpirome',
    'imipenem':'Imipenem','ipm':'Imipenem','imi':'Imipenem',
    'meropenem':'Meropenem','meropenom':'Meropenem','mem':'Meropenem',
    'ertapenem':'Ertapenem','etp':'Ertapenem','etrp':'Ertapenem',
    'gentamicin':'Gentamicin','gentamycin':'Gentamicin','gen':'Gentamicin','gm':'Gentamicin',
    'amikacin':'Amikacin','amk':'Amikacin','ak':'Amikacin','akm':'Amikacin',
    'streptomycin':'Streptomycin','sm':'Streptomycin',
    'ciprofloxacin':'Ciprofloxacin','cip':'Ciprofloxacin',
    'norfloxacin':'Norfloxacin','nor':'Norfloxacin',
    'nalidixic acid':'Nalidixic acid','nalidixic':'Nalidixic acid','na':'Nalidixic acid',
    'erythromycin':'Erythromycin','ery':'Erythromycin','e':'Erythromycin',
    'azithromycin':'Azithromycin','azm':'Azithromycin','azt':'Azithromycin',
    'clindamycin':'Clindamycin','clin':'Clindamycin','clm':'Clindamycin','cd':'Clindamycin',
    'chloramphenicol':'Chloramphenicol','chl':'Chloramphenicol','c':'Chloramphenicol',
    'co trimoxazole':'Co-trimoxazole','co-trimoxazole':'Co-trimoxazole','cotrimoxazole':'Co-trimoxazole','sxt':'Co-trimoxazole','cot':'Co-trimoxazole',
    'vancomycin':'Vancomycin','vanocomycin':'Vancomycin','van':'Vancomycin','va':'Vancomycin',
    'colistin':'Colistin','col':'Colistin',
    'nitrofurantoin':'Nitrofurantoin','nit':'Nitrofurantoin',
    'tigecycline':'Tigecycline','tgc':'Tigecycline',
    'tetracycline':'Tetracycline','tet':'Tetracycline',
    'linezolid':'Linezolid','lz':'Linezolid',
}

def parse_age(val):
    import pandas as pd, re
    if pd.isna(val): return pd.NA, pd.NA
    v = str(val).strip().lower()
    if v in {"", "nan", "na", "none", "null"}: return pd.NA, pd.NA
    v = re.sub(r'(?<=\d)(?=[a-z])', ' ', v)
    v = re.sub(r'(?<=[a-z])(?=\d)', ' ', v)
    v = re.sub(r'[^0-9a-z\s]', ' ', v)
    v = re.sub(r'\s+', ' ', v).strip()
    v = v.replace('monthsm', 'months')
    norms = [
        (r'\byears?\b|\byrs?\b|\by\b', 'y'),
        (r'\bmonths?\b|\bmnths?\b|\bmths?\b|\bmos?\b|\bmo\b', 'mo'),
        (r'\bweeks?\b|\bwks?\b|\bwk\b|\bw\b', 'w'),
        (r'\bdays?\b|\bdys?\b|\bdy\b|\bd\b', 'd'),
        (r'\bhours?\b|\bhrs?\b|\bhr\b|\bh\b', 'h'),
    ]
    for pat, rep in norms:
        v = re.sub(pat, rep, v)
    v = re.sub(r'(\d+)\s*m\b', r'\1 mo', v)
    pairs = re.findall(r'(\d+)\s*(y|mo|w|d|h)\b', v)
    if not pairs:
        return (float(v), "Years") if re.fullmatch(r'\d+', v) else (pd.NA, pd.NA)
    days = 0.0
    for n, u in pairs:
        n = float(n)
        days += {"y": n*365.25, "mo": n*30.4375, "w": n*7, "d": n, "h": n/24}[u]
    present = {u for _, u in pairs}
    if "y" in present:  return round(days/365.25, 3), "Years"
    if "mo" in present: return round(days/30.4375, 1), "Months"
    if "w" in present:  return round(days/7, 1), "Weeks"
    if "d" in present:  return round(days, 1), "Days"
    return round(days*24, 1), "Hours"

def clean_patienttype(val):
    import pandas as pd, re
    if pd.isna(val): return pd.NA
    v = re.sub(r'[^a-z]', '', str(val).strip().lower())
    if v in {"outpatient","outpatients","outpt","opd"} or v.startswith("outpat"):
        return "Outpatient"
    if v in {"inpatient","inpatients","inpt","ipd"} or v.startswith("inpat"):
        return "Inpatient"
    if v.startswith("out"): return "Outpatient"
    if v.startswith("in"):  return "Inpatient"
    return pd.NA

def clean_specimen(val):
    import pandas as pd, re
    if pd.isna(val): return pd.NA
    v = str(val).strip().lower().replace('_',' ').replace('-',' ')
    v = re.sub(r'\s+', ' ', v)
    if 'blood' in v:                      return 'Blood'
    if 'urine' in v:                      return 'Urine'
    if 'sputum' in v:                     return 'Sputum'
    if 'throat' in v and 'swab' in v:     return 'Throat swab'
    if 'tracheal' in v:                   return 'Tracheal aspirate'
    if 'catheter' in v and 'tip' in v:    return 'Catheter tip'
    if 'shunt' in v and 'tip' in v:       return 'Shunt tip'
    if 'ascitic' in v:                    return 'Ascitic fluid'
    if 'hydrocele' in v:                  return 'Hydrocele fluid'
    if 'genital' in v or 'urogenital' in v: return 'Genital swab'
    if 'pus' in v or 'purulent' in v:     return 'Pus'
    if 'lowresp' in v:                    return 'Lower respiratory (unspecified)'
    return v.title()

def clean_gender(val):
    import pandas as pd, re
    if pd.isna(val): return pd.NA
    v = re.sub(r'[^a-z]', '', str(val).strip().lower())
    if v == "": return pd.NA
    if v.startswith('m'): return "Male"
    if v.startswith('f'): return "Female"
    return pd.NA

def clean_sir(val):
    import pandas as pd, re
    if pd.isna(val): return pd.NA
    v = str(val).strip().lower()
    if v in {"", "na", "n/a", "none", "null"}: return pd.NA
    if v in {"i/s","s/i"}: return "I"
    if v.startswith('s'): return "S"
    if v.startswith('i'): return "I"
    if v.startswith('r'): return "R"
    m = re.search(r'\b([sir])\b', v)
    return m.group(1).upper() if m else pd.NA

def clean_antibiotic(val):
    import pandas as pd, re
    if pd.isna(val): return pd.NA
    s = str(val).strip()
    v = s.lower().replace('-', ' ')
    v = re.sub(r'\s+', ' ', v).strip()
    tokens = v.split()
    if v in ABX_MAP: return ABX_MAP[v]
    if 'amoxicillin' in tokens and 'clavulanic' in tokens: return 'Amoxicillin-clavulanate'
    if 'penicillin' in tokens and 'g' in tokens: return 'Penicillin G'
    for t in tokens:
        if t in ABX_MAP: return ABX_MAP[t]
    if 'cipro' in v: return 'Ciprofloxacin'
    if 'gentamyc' in v: return 'Gentamicin'
    if 'ceftriax' in v: return 'Ceftriaxone'
    if 'cefepim' in v: return 'Cefepime'
    if 'cefotax' in v: return 'Cefotaxime'
    if 'ceftazid' in v: return 'Ceftazidime'
    if 'cefurox' in v: return 'Cefuroxime'
    if 'meropen' in v: return 'Meropenem'
    if 'imipen' in v or 'ipm' in v: return 'Imipenem'
    if 'ertapen' in v: return 'Ertapenem'
    if 'vancom' in v: return 'Vancomycin'
    if 'azithro' in v: return 'Azithromycin'
    if 'erythro' in v: return 'Erythromycin'
    if 'clinda' in v: return 'Clindamycin'
    if 'chloramph' in v: return 'Chloramphenicol'
    if 'co trim' in v or 'cotrim' in v or 'sxt' in v: return 'Co-trimoxazole'
    if 'nalidix' in v: return 'Nalidixic acid'
    if 'norflox' in v or v == 'nor': return 'Norfloxacin'
    if v == 'pg': return 'Penicillin G'
    return pd.NA

def clean_pathogen(val):
    import pandas as pd, re
    if pd.isna(val): return pd.NA
    raw = str(val).strip()
    v = raw.lower()
    v = re.sub(r'[^a-z0-9\s]', ' ', v)
    v = re.sub(r'\s+', ' ', v).strip()
    vc = v.replace(' ','')
    code_map = {
        'klepne':'Klebsiella pneumoniae',
        'klepoxy':'Klebsiella oxytoca',
        'staaur':'Staphylococcus aureus',
        'staepi':'Staphylococcus epidermidis',
        'stasap':'Staphylococcus saprophyticus',
        'pseaer':'Pseudomonas aeruginosa',
        'entclo':'Enterobacter cloacae',
        'stenmal':'Stenotrophomonas maltophilia',
        'esccol':'Escherichia coli',
        'nlf':'Non-lactose fermenters (unspecified)',
        'nlfc':'Non-lactose fermenters (unspecified)',
        'lfc':'Lactose fermenters (unspecified)',
    }
    if vc in code_map: return code_map[vc]
    if 'klebsiella' in v and ('pneumon' in v or 'pnuemon' in v): return 'Klebsiella pneumoniae'
    if 'klebsiella' in v and 'oxytoca' in v: return 'Klebsiella oxytoca'
    if ('escherich' in v or 'eschericia' in v) and 'coli' in v: return 'Escherichia coli'
    if 'staphylococcus' in v and 'aure' in v: return 'Staphylococcus aureus'
    if 'staphylococcus' in v and ('epiderm' in v or 'epi' in v): return 'Staphylococcus epidermidis'
    if 'staphylococcus' in v and 'saproph' in v: return 'Staphylococcus saprophyticus'
    if 'streptococcus' in v and 'pneumon' in v: return 'Streptococcus pneumoniae'
    if 'salmonella typhi' in v: return 'Salmonella Typhi'
    if 'salmonella' in v and 'group d' in v: return 'Salmonella Group D'
    if 'pseudomonas' in v and 'aeruginosa' in v: return 'Pseudomonas aeruginosa'
    if 'enterobacter cloacae' in v: return 'Enterobacter cloacae'
    if 'enterobacter' in v: return 'Enterobacter spp'
    if 'neisseria' in v and 'gonorrhoe' in v: return 'Neisseria gonorrhoeae'
    if 'neisseria' in v and ('spp' in v or 'species' in v): return 'Neisseria spp'
    return raw.title()

def clean_year(val):
    import pandas as pd, re
    if pd.isna(val): return pd.NA
    s = str(val).strip()
    y = pd.to_datetime(s, errors='coerce', dayfirst=True)
    if pd.notna(y):
        yr = y.year
        if 1900 <= yr <= 2100: return int(yr)
    m = re.search(r'((?:19|20)\d{2})', s)
    return int(m.group(1)) if m else pd.NA
