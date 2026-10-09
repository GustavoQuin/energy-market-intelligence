import pandas as pd
import pyodbc

# ==========================================
# CONFIGURATION
# ==========================================

excel_path = r"C:\Users\gusta\Desktop\Proyectos para CV\Energy Project\Energy_Market_Intelligence_Dataset.xlsx"

server = r"GUSTAVOQUINTULE\SQLEXPRESS"
database = "EnergyMarketDB"

# ==========================================
# EXTRACT
# ==========================================

df = pd.read_excel(
    excel_path,
    sheet_name="DimDate"
)

print(f"Rows extracted from Excel: {len(df)}")
print(df.head())

# ==========================================
# TRANSFORM
# ==========================================

df["date_id"] = df["date_id"].astype(int)
df["date"] = pd.to_datetime(df["date"]).dt.date

df["year"] = df["year"].astype(int)
df["month"] = df["month"].astype(int)
df["week"] = df["week"].astype(int)
df["day"] = df["day"].astype(int)

df["quarter"] = df["quarter"].astype(str)
df["month_name"] = df["month_name"].astype(str)
df["day_name"] = df["day_name"].astype(str)

df["is_weekend"] = df["is_weekend"].astype(bool)

print("\nTransformation completed.")
print(df.dtypes)

# ==========================================
# CONNECT TO SQL SERVER
# ==========================================

drivers = pyodbc.drivers()

if "ODBC Driver 18 for SQL Server" in drivers:
    driver = "ODBC Driver 18 for SQL Server"
elif "ODBC Driver 17 for SQL Server" in drivers:
    driver = "ODBC Driver 17 for SQL Server"
else:
    raise Exception("ODBC Driver 17/18 for SQL Server was not found.")

connection_string = (
    f"DRIVER={{{driver}}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

print("\nConnected successfully to SQL Server.")

# ==========================================
# VALIDATE TARGET TABLE
# ==========================================

cursor.execute("SELECT COUNT(*) FROM dbo.DimDate")
existing_rows = cursor.fetchone()[0]

if existing_rows > 0:
    cursor.close()
    conn.close()

    raise Exception(
        f"dbo.DimDate already contains {existing_rows} rows. "
        "Load cancelled to prevent duplicate primary keys."
    )

# ==========================================
# LOAD
# ==========================================

insert_query = """
INSERT INTO dbo.DimDate (
    date_id,
    [date],
    [year],
    [quarter],
    [month],
    month_name,
    [week],
    [day],
    day_name,
    is_weekend
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

records = [
    (
        int(row.date_id),
        row.date,
        int(row.year),
        row.quarter,
        int(row.month),
        row.month_name,
        int(row.week),
        int(row.day),
        row.day_name,
        int(row.is_weekend)
    )
    for row in df.itertuples(index=False)
]

cursor.fast_executemany = True
cursor.executemany(insert_query, records)

conn.commit()

# ==========================================
# VALIDATION
# ==========================================

cursor.execute("SELECT COUNT(*) FROM dbo.DimDate")
sql_rows = cursor.fetchone()[0]

print(f"\nRows loaded into SQL Server: {sql_rows}")

if sql_rows == len(df):
    print("VALIDATION OK: Excel and SQL row counts match.")
else:
    print("WARNING: Row counts do not match.")

cursor.close()
conn.close()

print("\nDimDate ETL completed successfully.")

