# server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from workflow import DatabaseAnalysisGraph  # Import the new class
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitSDK, Action as CopilotAction, LangGraphAgent
from copilotkit.langchain import copilotkit_messages_to_langchain
import routes


app = FastAPI(title="Property Data API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    text: str

# Initialize the graph
try:
    graph_instance = DatabaseAnalysisGraph()
except Exception as e:
    print(f"Error initializing graph: {str(e)}")
    graph_instance = None

# Initialize the CopilotKit SDK with your LangGraph agent
sdk = CopilotKitSDK(
    agents=[
        LangGraphAgent(
            name="Property_analysis_agent",
            description="Agent that analyzes Real Estate Property and associated contact data and answers questions",
            graph=graph_instance.graph if graph_instance else None,
            copilotkit_config={
                "convert_messages": copilotkit_messages_to_langchain(use_function_call=True)
            }
        )
    ]
)

# Add the CopilotKit endpoint
add_fastapi_endpoint(app, sdk, "/copilotkit_remote")

# Include the API routes
app.include_router(routes.router)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8001, reload=True)


