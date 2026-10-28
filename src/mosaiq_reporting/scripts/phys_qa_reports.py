
import pyodbc
import pandas as pd
from datetime import datetime

# ============================================================
# MOSAIQ connection and report settings
# ============================================================

MOSAIQ_DB = {
    "DRIVER": "SQL Server",
    "SERVER": "OHICPRPTSQL01",
    "DATABASE": "MOSAIQ",
    "Trusted_Connection": "yes",
}

CUTOFF_DATE = "2026-07-01"
QUESTION_ID = 60189
PHYSICS_QA_VIEW_ID = 53352

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
excel_file = f"Physics_QA_Report_{timestamp}.xlsx"

cnxn = pyodbc.connect(
    "DRIVER={{{}}};SERVER={};DATABASE={};Trusted_Connection={}".format(
        MOSAIQ_DB["DRIVER"],
        MOSAIQ_DB["SERVER"],
        MOSAIQ_DB["DATABASE"],
        MOSAIQ_DB["Trusted_Connection"],
    )
)

try:
    # ========================================================
    # 1. Overall answer tally (all time)
    # ========================================================

    query_overall = f"""
        SELECT
            d.OBD_ID AS Answer_ID,
            d.Label AS Answer_Text,
            COUNT(*) AS Count
        FROM dbo.Observe o
        INNER JOIN dbo.ObsReq r
            ON o.OBR_SET_ID = r.OBR_ID
        INNER JOIN dbo.ObsDef d
            ON o.Obs_Choice = d.OBD_ID
        WHERE o.OBD_ID = {QUESTION_ID}
          AND r.View_OBD_ID = {PHYSICS_QA_VIEW_ID}
        GROUP BY
            d.OBD_ID,
            d.Label
        ORDER BY
            COUNT(*) DESC,
            d.Label;
    """

    overall = pd.read_sql_query(query_overall, cnxn)

    print("\n=== Overall answer tally (all time) ===")
    print(overall.to_string(index=False))

    # ========================================================
    # 2. Monthly answer tally since July 1, 2026
    # ========================================================

    query_monthly = f"""
        SELECT
            YEAR(r.Obs_DtTm) AS Year,
            MONTH(r.Obs_DtTm) AS Month,
            d.OBD_ID AS Answer_ID,
            d.Label AS Answer_Text,
            COUNT(*) AS Count
        FROM dbo.Observe o
        INNER JOIN dbo.ObsReq r
            ON o.OBR_SET_ID = r.OBR_ID
        INNER JOIN dbo.ObsDef d
            ON o.Obs_Choice = d.OBD_ID
        WHERE o.OBD_ID = {QUESTION_ID}
          AND r.View_OBD_ID = {PHYSICS_QA_VIEW_ID}
        GROUP BY
            YEAR(r.Obs_DtTm),
            MONTH(r.Obs_DtTm),
            d.OBD_ID,
            d.Label
        ORDER BY
            YEAR(r.Obs_DtTm),
            MONTH(r.Obs_DtTm),
            d.Label;
    """

    monthly = pd.read_sql_query(query_monthly, cnxn)

    if not monthly.empty:
        monthly["Year-Month"] = (
            monthly["Year"].astype(str)
            + "-"
            + monthly["Month"].astype(str).str.zfill(2)
        )
        monthly = monthly[
            [
                "Year-Month",
                "Year",
                "Month",
                "Answer_ID",
                "Answer_Text",
                "Count",
            ]
        ]

    print("\n=== Monthly answer tally (since July 1, 2026) ===")
    print(monthly.to_string(index=False))

    # ========================================================
    # 3. Physics QA form usage since July 1, 2026
    #    This table does not contain answer categories.
    # ========================================================

    query_forms = f"""
        SELECT
            COUNT(DISTINCT r.OBR_ID) AS FormsSinceCutoff,
            MIN(r.Obs_DtTm) AS EarliestObsDate,
            MAX(r.Obs_DtTm) AS LatestObsDate
        FROM dbo.ObsReq r
        WHERE r.View_OBD_ID = {PHYSICS_QA_VIEW_ID}
          AND r.Obs_DtTm >= '{CUTOFF_DATE}';
    """

    forms = pd.read_sql_query(query_forms, cnxn)

    print("\n=== Physics QA form usage (since July 1, 2026) ===")
    print(forms.to_string(index=False))

    # ========================================================
    # 4. Detailed answer records since July 1, 2026
    # ========================================================

    query_details = f"""
        SELECT
            o.OBX_ID,
            o.OBD_ID AS Question_ID,
            d.OBD_ID AS Answer_ID,
            d.Label AS Answer_Text,
            o.OBR_SET_ID,
            r.Obs_DtTm
        FROM dbo.Observe o
        INNER JOIN dbo.ObsReq r
            ON o.OBR_SET_ID = r.OBR_ID
        INNER JOIN dbo.ObsDef d
            ON o.Obs_Choice = d.OBD_ID
        WHERE o.OBD_ID = {QUESTION_ID}
          AND r.View_OBD_ID = {PHYSICS_QA_VIEW_ID}
          AND r.Obs_DtTm >= '{CUTOFF_DATE}'
        ORDER BY
            r.Obs_DtTm,
            o.OBX_ID;
    """

    details = pd.read_sql_query(query_details, cnxn)

    print("\n=== Detailed answer records (since July 1, 2026) ===")
    print(details.to_string(index=False))

    # ========================================================
    # 5. Export CSV files
    # ========================================================

    overall.to_csv(
        f"Physics_QA_Overall_Tally_{timestamp}.csv",
        index=False,
    )

    monthly.to_csv(
        f"Physics_QA_Monthly_Tally_{timestamp}.csv",
        index=False,
    )

    forms.to_csv(
        f"Physics_QA_Form_Usage_{timestamp}.csv",
        index=False,
    )

    details.to_csv(
        f"Physics_QA_Detailed_Records_{timestamp}.csv",
        index=False,
    )

    # ========================================================
    # 6. Export Excel workbook
    # ========================================================

    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        overall.to_excel(
            writer,
            sheet_name="Overall Tally",
            index=False,
        )

        monthly.to_excel(
            writer,
            sheet_name="Monthly Tally",
            index=False,
        )

        forms.to_excel(
            writer,
            sheet_name="Form Usage",
            index=False,
        )

        details.to_excel(
            writer,
            sheet_name="Detailed Records",
            index=False,
        )

    print(f"\nExcel report saved to: {excel_file}")
    print("All CSV exports completed.")

finally:
    cnxn.close()


