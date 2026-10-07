# -*- coding: utf-8 -*-
"""
Created on Tue Aug 19 13:53:30 2025

@author: mlamey

This script returns patient shifts performed after Imaging
examples are given below on how to filter and plot the data returned
The query returns a lot of data, and although the query is quick it is 
likely best to keep the start to end dates less than one year

EV feedback - the acquisition time in Mosaiq corresponds to the 
Offset.Study_DtTm variable in the Offset table

"""

from datetime import datetime, timedelta
import pandas.io.sql as psql
import pandas as pd
import pyodbc
import matplotlib.pyplot as plt

import warnings
warnings.filterwarnings('ignore') # gets rid of pandas SQLAlchemy warnings

MOSAIQ_DB = {
    'DRIVER': 'SQL Server',
    'SERVER': 'OHICPRPTSQL01',
    'DATABASE': 'MOSAIQ',
    'Trusted_Connection': 'yes',
}

# Offset.Offset_Type = 3 ensure it is a shift from an image match
# Offset.Offset_Type = 1 is the auto shifts from setup to ISO
def get_mosaiq_shifts(start_date, end_date):
    
    cnxn = pyodbc.connect('DRIVER={{{}}};SERVER={};DATABASE={};Trusted_Connection={}{}'.format(
        MOSAIQ_DB['DRIVER'],
        MOSAIQ_DB['SERVER'],
        MOSAIQ_DB['DATABASE'],
        MOSAIQ_DB['Trusted_Connection'],
        ';UID={};PWD={}'.format(MOSAIQ_DB['USERNAME'], MOSAIQ_DB['PASSWORD']) if 'USERNAME' in MOSAIQ_DB else ''
    ))
    cursor = cnxn.cursor()
    
    query = """SELECT
        Ident.IDA,
        Ident.IDA as patID,
        Patient.Last_name,
        Patient.First_name,
        Site.Site_name,               
        PatCPlan.Course,
        Site.Dose_Ttl,
        Site.Fractions,
        CPlan.CPlan_Name,
        Offset.Edit_DtTm,
        Offset.Study_DtTm,
        Offset.Superior_Offset,
        Offset.Anterior_Offset,
        Offset.Lateral_Offset,
        Offset.Angle_Offset,
        Offset.Pitch_Offset,
        Offset.Roll_Offset

        FROM Patient
        INNER JOIN Ident ON Patient.Pat_ID1 = Ident.Pat_ID1
        INNER JOIN PatCPlan ON PatCPlan.Pat_ID1 = Patient.Pat_ID1
        INNER JOIN CPlan ON CPlan.CPL_ID = PatCPlan.CPL_ID
        INNER JOIN Site ON Site.PCP_ID = PatCPlan.PCP_ID
        INNER JOIN Offset ON Offset.Sit_Set_ID = Site.SIT_ID

        WHERE Site.Edit_DtTm >= '{0}'
        AND Site.Edit_DtTm <= '{1}'
        AND Site.Version = 0
        AND Offset.Offset_Type = 3

        ORDER BY Site_name

    """.format(start_date, end_date)
    
    df = psql.read_sql(query, cnxn)
    return df

# NOTE query gets all shifts for all patients so doing more than one year is ill-advised
start_date = '2025-01-01' # YYYY-MM-DD
end_date = '2025-08-20' # YYYY-MM-DD
all_shifts = get_mosaiq_shifts(start_date, end_date)

# remove QA patients - technically remove patient whose ID has non-numeric characters in it
aps = all_shifts[ all_shifts['patID'].str.isdigit() ] # ps - all patient shifts

# filter all shifts based on a list of sites
sites = ['LUNR', 'LUNL']
fs = aps.loc[aps['Site_name'].apply(lambda x: any(s in x for s in sites) )] # fs for filtered shifts

# filter by care plan name containing
sub_cp_name = 'Lymphoma' # make string longer if you want specific CP
fs_cp = aps.loc[aps['CPlan_Name'].apply(lambda x: sub_cp_name in x )]

# For all the code below if you're only interested in a specific site you could 
# replace 'aps' with 'fs' the list of shifts filtered by site

# How to get all lateral shifts > 2cm
# positive is left
big_Lat_shifts = aps.query('(Lateral_Offset > 2) or (Lateral_Offset < -2)')

# How to get all vector magnitude shift > 2.5cm
big_shifts = aps[ aps['Lateral_Offset']*aps['Lateral_Offset'] + aps['Superior_Offset']*aps['Superior_Offset'] +
                aps['Anterior_Offset']*aps['Anterior_Offset'] > 2.5*2.5]

# how to get the average anterior shift
avg_ant_shift_aps = aps['Anterior_Offset'].mean()
avg_sup_shift_aps= aps['Superior_Offset'].mean()
avg_lat_shift_aps = aps['Lateral_Offset'].mean()

# Plot shifts for all patients
ax = aps['Superior_Offset'].hist(bins=51, range=(-2.5,2.5)) # only plot from -2.5cm to + 2.5cm in 1mm bins
ax.set_xlabel('Shift (cm)',  fontsize = 12)
ax.set_ylabel('Count', fontsize = 12)
ax.set_title('Post Imaging Sup-Inf Shifts (Sup is +ve)', fontsize = 12)
plt.show()

ax = aps['Anterior_Offset'].hist(bins=51, range=(-2.5,2.5)) # only plot from -2.5cm to + 2.5cm in 1mm bins
ax.set_xlabel('Shift (cm)',  fontsize = 12)
ax.set_ylabel('Count', fontsize = 12)
ax.set_title('Post Imaging Ant-Post Shifts (Ant is +ve)', fontsize = 12)
plt.show()

ax = aps['Lateral_Offset'].hist(bins=51, range=(-2.5,2.5)) # only plot from -2.5cm to + 2.5cm in 1mm bins
ax.set_xlabel('Shift (cm)',  fontsize = 12)
ax.set_ylabel('Count', fontsize = 12)
ax.set_title('Post Imaging Lat Shifts (Left is +ve)', fontsize = 12)
plt.show()

del MOSAIQ_DB, start_date, end_date
# save to csv
#aps.to_csv(file_name, sep=',')
