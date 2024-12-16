# tools.py
from typing import Optional, Type, Dict, List
from langchain.tools import BaseTool
from pydantic import BaseModel, Field 
from langchain_core.tools import ToolException
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import create_engine
from langchain_core.tools import tool
import config

from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine

import pyodbc
import config


def get_db_connection():
    # Create service principal ID using config variables
    service_principal_id = f"{config.CLIENT_ID}@{config.TENANT_ID}"

    # Define the connection string
    conn_str = (
        f"mssql+pyodbc://{service_principal_id}:{config.CLIENT_SECRET}@{config.FABRIC_SERVER}"
        f"/{config.FABRIC_DATABASE}?"
        "driver=ODBC+Driver+18+for+SQL+Server&"
        "Authentication=ActiveDirectoryServicePrincipal&"
        "Encrypt=yes&"
        "TrustServerCertificate=yes&"
        f"TenantId={config.TENANT_ID}&"
        "MultiSubnetFailover=Yes&"
        "ApplicationIntent=ReadWrite"
    )

    # Create SQLAlchemy engine
    engine = create_engine(conn_str)
    
    # Create SQLDatabase instance
    return SQLDatabase(engine)

def get_sql_toolkit():
    """Get SQL toolkit with all necessary tools."""
    db = get_db_connection()
    if db is None:
        raise ConnectionError("Failed to establish database connection")
        
    llm = ChatOpenAI(temperature=0, model="gpt-4")
    return SQLDatabaseToolkit(db=db, llm=llm)