import os
from dotenv import load_dotenv

#Loading env variables
load_dotenv()


TENANT_ID=os.getenv('TENANT_ID')
CLIENT_ID=os.getenv('CLIENT_ID')
CLIENT_SECRET= os.getenv('CLIENT_SECRET')
FABRIC_SERVER=os.getenv('FABRIC_SERVER')
FABRIC_DATABASE=os.getenv('FABRIC_DATABASE')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")



# Validate essential configuration
if not TENANT_ID:
    raise ValueError("TENANT_ID is not set in the environment variables")

if not CLIENT_ID:
    raise ValueError("CLIENT_ID is not set in the environment variables")


if not CLIENT_SECRET:
    raise ValueError("CLIENT_SECRET is not set in the environment variables")


if not FABRIC_SERVER:
    raise ValueError("FABRIC_SERVER is not set in the environment variables")

if not FABRIC_DATABASE:
    raise ValueError("FABRIC_DATABASE is not set in the environment variables")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables")

