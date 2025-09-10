import pandas as pd

def get_demo_df():
    return pd.DataFrame({
        'YEAR':[2025,2025,2025,2025,2025,2025],
        'PATIENT_ID':['Bu25-1-03','Bu25-1-04','AA-1','AA-2','AA-3','AA-4'],
        'AGE':['1yr 7 months','28YRS','6DYS','3MONTHS','45yrs','10YRS'],
        'GENDER':['M','F','m','.','F','M'],
        'PATIENTTYPE':['OUTPATIENT','INPATENT','Outpatient','Inpatient','OUTPATIENT','Inpatient'],
        'SAMPLE_DATE':['07/01/2025','2025-02-11','2025-03-09','2025-03-11','2025-04-01','2025-04-02'],
        'SPECIMEN':['urine','BLOOD','throat swab','LOWRESP-','urine','sputum'],
        'PATHOGEN':['KLEPNE','Escherichia coli','Staphylococcus aureus','PSEAER','Klebsiella pneumoniae','Citrobacter freundii'],
        'ANTIBIOTIC':['CIP','ceftriaxone','gentamicin','MEROPENOM','CIP','AMK'],
        'SIR':['S','R','I/S','S-Susceptible','R','S'],
        'FACILITY':['Central Hospital','Central Hospital','West Clinic','West Clinic','Central Hospital','West Clinic'],
        'HCF_ID':['CH-01','CH-01','WC-02','WC-02','CH-01','WC-02']
    })
