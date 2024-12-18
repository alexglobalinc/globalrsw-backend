#import config
import random
import os
#from .workflow import DatabaseAnalysisGraph
#from workflow import DatabaseAnalysisGraph
import asyncio

from openai import OpenAI

import sys

#client = OpenAI(api_key = config.OPENAI_API_KEY)


# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow import DatabaseAnalysisGraph
import asyncio
#import config

def call_model(question: str) -> str:
    """Synchronous function to call the SQL database agent"""
    # Create event loop and run async function
    async def run_query():
        graph = DatabaseAnalysisGraph()
        result = await graph.run(question)
        # Extract the last message content
        if result and "messages" in result and result["messages"]:
            return result["messages"][-1].content
        return "No response generated"

    # Run the async function in the event loop
    try:
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        response = loop.run_until_complete(run_query())
        return response
    except Exception as e:
        print(f"Error in call_model: {str(e)}")
        return f"Error processing query: {str(e)}"