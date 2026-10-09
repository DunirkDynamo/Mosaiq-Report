"""
This query gets the number of Care plans used over a specified time period.

Only gets care plans from approved RadRx.

It also gets all currently approved care plans and produces a count
for how many times each has been used during the specified period.
"""

import pandas as pd
import pandas.io.sql as psql
import warnings

from mosaiq_reporting.connection import MosaiqConnection

warnings.filterwarnings('ignore')


def get_care_plans(start_date, end_date):
    db = MosaiqConnection()
    db.connect()

    try:
        query = """
            SELECT
                Ident.IDA,
                Ident.IDA AS patID,
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
            WHERE Site.Edit_DtTm >= ?
                AND Site.Edit_DtTm <= ?
                AND Site.Status_Enum = 5
            ORDER BY Site.Edit_DtTm
        """

        df = psql.read_sql(
            query,
            db.cnxn,
            params=[start_date, end_date]
        )

        return df.set_index('IDA')

    finally:
        db.close()


def get_approved_care_plans():
    db = MosaiqConnection()
    db.connect()

    try:
        query = """
            SELECT
                CPlan.Category,
                CPlan.CPlan_Name
            FROM CPlan
            WHERE CPlan.Status_Enum = 5
                AND CPlan.Version = 0
            ORDER BY CPlan.Category
        """

        df = psql.read_sql(query, db.cnxn)

        return df

    finally:
        db.close()


start_date = '2025-01-01'  # YYYY-MM-DD
end_date = '2026-09-24'    # YYYY-MM-DD

my_data = get_care_plans(start_date, end_date)

# Count usage of each unique care plan during the selected period.
unique_cp = my_data['CPlan_Name'].value_counts()

# Get all currently approved care plans.
approved_cp = get_approved_care_plans()

# Add a usage count for each currently approved care plan.
approved_cp['Count'] = 0

for plan_name in my_data['CPlan_Name']:
    approved_cp.loc[
        approved_cp['CPlan_Name'] == plan_name,
        'Count'
    ] += 1

# Export the results to CSV files.
my_data.to_csv(
    f'careplan_usuage_{start_date}-to-{end_date}.csv'
)

approved_cp.to_csv(
    f'approved_careplans_{start_date}-to-{end_date}.csv',
    index=False
)

unique_cp.to_csv(
    f'unique_careplans_{start_date}-to-{end_date}.csv'
)

