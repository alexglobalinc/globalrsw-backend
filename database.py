import pyodbc
import config

def get_db_connection():
    # Create service principal ID using config variables
    service_principal_id = f"{config.CLIENT_ID}@{config.TENANT_ID}"

    # Define the connection string using config variables
    conn_str = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={config.FABRIC_SERVER};"
        f"Database={config.FABRIC_DATABASE};"
        f"UID={service_principal_id};"
        f"PWD={config.CLIENT_SECRET};"
        "Authentication=ActiveDirectoryServicePrincipal;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        f"TenantId={config.TENANT_ID};"
        "MultiSubnetFailover=Yes;"
        "ApplicationIntent=ReadWrite"
    )

    return pyodbc.connect(conn_str)

def execute_query(query):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            results = cursor.fetchall()
            return [dict(zip(columns, row)) for row in results]
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

# Example usage
if __name__ == "__main__":
    query = "SELECT TOP 5 * FROM [dbo].[contact]"
    results = execute_query(query)
    if results:
        print(results)