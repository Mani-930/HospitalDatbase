import pyodbc

DRIVER_NAME = "ODBC Driver 17 for SQL Server"
SERVER_NAME = "MANI\\SQLEXPRESS"
DATABASE_NAME = "HospitalMgmtDB"

connection_string = (
    f"DRIVER={{{DRIVER_NAME}}};"
    f"SERVER={SERVER_NAME};"
    f"DATABASE={DATABASE_NAME};"
    "Trusted_Connection=yes;"
)

try:
    conn = pyodbc.connect(connection_string)
    print("✅ Connected to SQL Server successfully!")
except Exception as e:
    print("❌ Error connecting:", e)


