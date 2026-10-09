# -*- coding: utf-8 -*-
"""
Created on Thu Aug 21 10:45:51 2025

@author: mlamey

This query gets the number of Care plans used over a specified time period
Only gets care plans from approved RadRx

It also gets all currently approved care plans and produces a count
for how many times each has been used this year

"""

from datetime import datetime, timedelta
import pandas.io.sql as psql
import pandas as pd
import pyodbc

import warnings
warnings.filterwarnings('ignore') # gets rid of pandas SQLAlchemy warnings

MOSAIQ_DB = {
    'DRIVER': 'SQL Server',
    'SERVER': 'OHICPRPTSQL01',
    'DATABASE': 'MOSAIQ',
    'Trusted_Connection': 'yes',
}


def get_care_plans(start_date, end_date):
    
    #days_ago_string = '2025-01-09'
    #start_date = datetime.now() - timedelta(30)
    days_ago = (datetime.now() + timedelta(days=-700))
    days_ago_string = str(days_ago.date())
    
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
        Site.Dose_Ttl,
        Site.Fractions,
        Site.Status_Enum,
        Site.Edit_DtTm,
        CPlan.CPlan_Name
        
        FROM Site
        INNER JOIN PatCPlan ON PatCPlan.PCP_ID = Site.PCP_ID
        INNER JOIN Patient ON Patient.Pat_ID1 = PatCPlan.Pat_ID1
        INNER JOIN Ident ON Ident.Pat_ID1 = Patient.Pat_ID1
        INNER JOIN CPlan ON CPlan.CPL_ID = PatCPlan.CPL_ID
        
        WHERE Site.Edit_DtTm >= '{0}'
        AND  Site.Edit_DtTm < ='{1}'
        AND Site.Status_Enum = 5
            
        ORDER BY Site.Edit_DtTm
    
    """.format(start_date, end_date)

    df = psql.read_sql(query, cnxn)

    df.reset_index()

    indexed_df = df.set_index(['IDA'])

    return indexed_df

def get_approved_care_plans():
    cnxn = pyodbc.connect('DRIVER={{{}}};SERVER={};DATABASE={};Trusted_Connection={}{}'.format(
        MOSAIQ_DB['DRIVER'],
        MOSAIQ_DB['SERVER'],
        MOSAIQ_DB['DATABASE'],
        MOSAIQ_DB['Trusted_Connection'],
        ';UID={};PWD={}'.format(MOSAIQ_DB['USERNAME'], MOSAIQ_DB['PASSWORD']) if 'USERNAME' in MOSAIQ_DB else ''
    ))
    cursor = cnxn.cursor()
    
    query = """SELECT
        CPlan.Category,
        CPlan.CPlan_Name
     
        FROM CPlan
        
        WHERE CPlan.Status_Enum=5
        AND CPlan.Version = 0
            
        ORDER BY CPlan.Category
    
    """

    df = psql.read_sql(query, cnxn)

    return df

start_date = '2025-01-01' # YYY-MM-DD
end_date = '2026-09-24' # YYY-MM-DD

my_data = get_care_plans(start_date, end_date)
# below is a list of all unique CP names and a count for usage for above time range
# may include older CP that are no longer approved or older versions
unique_cp = my_data['CPlan_Name'].value_counts() 

# Below is a list of our currently approved care plans
# These are the CP that end users see in Mosaiq
approved_cp = get_approved_care_plans()
# this will be currently approved cp with usage count, add a column at the end
approved_cp['Count'] = pd.Series(0,index=approved_cp.index) 

# For the currently approved care plans, count how many times
# it has been used in the above time frame
for i in range(len(my_data)):
    approved_cp.loc[approved_cp['CPlan_Name'] == my_data['CPlan_Name'][i], 'Count'] +=1

my_data.to_csv('careplan_usuage_' + start_date + '-to-' + end_date + '.csv', sep=',')
approved_cp.to_csv('approved_careplans_'+ start_date + '-to-'  + end_date + '.csv', sep=',')
unique_cp.to_csv('unique_careplans_'+ start_date + '-to-'  + end_date + '.csv', sep=',')

del i, end_date, start_date, MOSAIQ_DB

