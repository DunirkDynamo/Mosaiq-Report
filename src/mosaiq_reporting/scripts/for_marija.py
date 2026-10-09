import pandas.io.sql as psql

from mosaiq_reporting.connection import MosaiqConnection


db = MosaiqConnection()
db.connect()

try:
    query = """
        SELECT
            s.name AS Schema_Name,
            t.name AS Table_Name,
            c.name AS Column_Name,
            ty.name AS Data_Type
        FROM sys.tables AS t
        INNER JOIN sys.schemas AS s
            ON s.schema_id = t.schema_id
        INNER JOIN sys.columns AS c
            ON c.object_id = t.object_id
        INNER JOIN sys.types AS ty
            ON ty.user_type_id = c.user_type_id
        WHERE
            t.name LIKE '%Physics%'
            OR t.name LIKE '%QA%'
            OR t.name LIKE '%Checklist%'
            OR c.name LIKE '%subsequent%'
            OR c.name LIKE '%course%'
            OR c.name LIKE '%Physics%'
            OR c.name LIKE '%QA%'
        ORDER BY
            s.name,
            t.name,
            c.column_id
    """

    results = psql.read_sql(query, db.cnxn)

    print(results.to_string(index=False))

finally:
    db.close()

