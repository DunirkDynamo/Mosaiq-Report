import pyodbc
import pandas as pd

MOSAIQ_DB = {
    "DRIVER": "SQL Server",
    "SERVER": "OHICPRPTSQL01",
    "DATABASE": "MOSAIQ",
    "Trusted_Connection": "yes",
}

cnxn = pyodbc.connect(
    "DRIVER={{{}}};SERVER={};DATABASE={};Trusted_Connection={}".format(
        MOSAIQ_DB["DRIVER"],
        MOSAIQ_DB["SERVER"],
        MOSAIQ_DB["DATABASE"],
        MOSAIQ_DB["Trusted_Connection"],
    )
)

try:
    # Examine the ObsReq dates associated with question 60189
    query = """
        SELECT
            COUNT(*) AS TotalRecords,

            SUM(CASE WHEN r.Create_DtTm IS NOT NULL
                     THEN 1 ELSE 0 END) AS CreateDate_Count,
            MIN(r.Create_DtTm) AS CreateDate_Min,
            MAX(r.Create_DtTm) AS CreateDate_Max,

            SUM(CASE WHEN r.Edit_DtTm IS NOT NULL
                     THEN 1 ELSE 0 END) AS EditDate_Count,
            MIN(r.Edit_DtTm) AS EditDate_Min,
            MAX(r.Edit_DtTm) AS EditDate_Max,

            SUM(CASE WHEN r.Obs_DtTm IS NOT NULL
                     THEN 1 ELSE 0 END) AS ObsDate_Count,
            MIN(r.Obs_DtTm) AS ObsDate_Min,
            MAX(r.Obs_DtTm) AS ObsDate_Max,

            SUM(CASE WHEN r.Results_DtTm IS NOT NULL
                     THEN 1 ELSE 0 END) AS ResultsDate_Count,
            MIN(r.Results_DtTm) AS ResultsDate_Min,
            MAX(r.Results_DtTm) AS ResultsDate_Max,

            SUM(CASE WHEN r.Sanct_DtTm IS NOT NULL
                     THEN 1 ELSE 0 END) AS SanctDate_Count,
            MIN(r.Sanct_DtTm) AS SanctDate_Min,
            MAX(r.Sanct_DtTm) AS SanctDate_Max,

            SUM(CASE WHEN r.Sch_DtTm IS NOT NULL
                     THEN 1 ELSE 0 END) AS ScheduledDate_Count,
            MIN(r.Sch_DtTm) AS ScheduledDate_Min,
            MAX(r.Sch_DtTm) AS ScheduledDate_Max

        FROM dbo.Observe o
        INNER JOIN dbo.ObsReq r
            ON o.OBR_SET_ID = r.OBR_ID
        WHERE o.OBD_ID = 60189
          AND r.View_OBD_ID = 53352
    """

    results = pd.read_sql_query(query, cnxn)

    print("\n=== Date-field summary for Physics QA question 60189 ===")
    print(results.to_string(index=False))

    results.to_csv("MOSAIQ_QA_Date_Summary.csv", index=False)

    # Inspect individual records and their dates
    query_details = """
        SELECT TOP 50
            o.OBX_ID,
            o.OBD_ID,
            o.OBR_SET_ID,
            r.View_OBD_ID,
            r.Create_DtTm,
            r.Edit_DtTm,
            r.Obs_DtTm,
            r.Results_DtTm,
            r.Sanct_DtTm,
            r.Sch_DtTm,
            r.Obs_End_DtTm,
            r.Rcvd_DtTm
        FROM dbo.Observe o
        INNER JOIN dbo.ObsReq r
            ON o.OBR_SET_ID = r.OBR_ID
        WHERE o.OBD_ID = 60189
          AND r.View_OBD_ID = 53352
        ORDER BY r.Create_DtTm DESC
    """

    details = pd.read_sql_query(query_details, cnxn)

    print("\n=== Sample records and associated dates ===")
    print(details.to_string(index=False))

    details.to_csv("MOSAIQ_QA_Date_Details.csv", index=False)

finally:
    cnxn.close()